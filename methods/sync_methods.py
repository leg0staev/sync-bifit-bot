from collections import namedtuple
from typing import Generator, Union
from zipfile import BadZipFile

import openpyxl

from Clases.ApiMarketplaces.Ali.ALIapi import AliApi
from Clases.ApiMarketplaces.Ozon.OzonApi import OzonApi
from Clases.ApiMarketplaces.Ozon.OzonProdResponse import OzonProdResponse
from Clases.ApiMarketplaces.Ozon.Posting import Posting
from Clases.ApiMarketplaces.Ozon.Warehouse import Warehouse
from Clases.ApiMarketplaces.Vk.VKProduct import VkProduct
from Clases.ApiMarketplaces.Vk.VkApi import VkApi
from Clases.ApiMarketplaces.Vk.VkProdResponce import VkProdResponse
from Clases.ApiMarketplaces.Ya.YAapi import YAapi
from Clases.BifitApi.AuthReq import *
from Clases.BifitApi.Good import Good
from Clases.BifitApi.Goods import *
from Clases.BifitApi.GoodsListReq import *
from Clases.BifitApi.Nomenclature import *
from Clases.BifitApi.OrgListReq import *
from Clases.BifitApi.Organization import *
from Clases.BifitApi.TradeObjListReq import TradeObjListReq
from Clases.BifitApi.TradeObject import *
from logger import logger


def get_bifit_token(username: str, pswd: bytes) -> str:
    auth_json = AuthReq(username=username, password=pswd).send_post()
    return auth_json['access_token']


def get_bifit_org_list(token: str) -> list[Organization]:
    return [Organization(org) for org in OrgListReq(token=token).send_post()]


def get_bifit_trade_obj_list(token: str, org_id: str) -> list[TradeObject]:
    return [TradeObject(obj) for obj in TradeObjListReq(token=token, org_id=org_id).send_post()]


def get_bifit_products_list(token: str, org_id: str, obj_id: str) -> list[Good]:
    goods_list = GoodsListReq(token=token, org_id=org_id, trade_obj_id=obj_id).send_post()
    products = [Good(Goods(item['goods']), Nomenclature(item['nomenclature'])) for item in goods_list]
    return products


def get_markets_products(products_set: set[Good]) -> tuple:
    logger.debug('get_markets_products started')

    ya_goods: dict[str:int] = {}
    ali_goods: dict[str:int] = {}
    vk_goods: dict[str:int] = {}
    ozon_goods: dict[str:int] = {}

    for product in products_set:
        try:
            markets: list[str] = product.nomenclature.vendor_code.split("-")
            # print(markets)
            if "ya" in markets:
                ya_goods[product.nomenclature.barcode] = product.goods.quantity
            if "oz" in markets:
                ozon_goods[product.nomenclature.barcode] = product.goods.quantity
            if "ali" in markets:
                ali_goods[product.nomenclature.barcode] = product.goods.quantity
            if "sber" in markets:
                pass
            if "vk" in markets:
                vk_goods[product.nomenclature.barcode] = product.goods.quantity
        except AttributeError:
            # print(f"Ошибка: товар {product.get_name()}")
            continue
    return ya_goods, ali_goods, vk_goods, ozon_goods


def parse_calculation(string: str) -> \
        (tuple[dict[str, tuple[str, int]], set[tuple[str, int]]], set[str] | tuple[None, None, None]):
    """парсит расчет"""
    logger.debug('начал parse_calculation')
    lines = string.strip().split('\n')
    template = '№ п/п  наименование  штрих код  -  цена за ед    -  кол-во    -  всего'
    if template not in lines[0]:
        logger.debug('строка не сходится с шаблоном')
        return None, None, None
    logger.debug('рассчет получил')

    to_write_off = dict()
    no_barcode = set()
    no_quantity = set()

    for line in lines[1:]:

        specifications = line.split(' - ')
        number_with_name, barcode = specifications[0].rsplit('  ', 1)
        number, name = number_with_name.split('  ', 1)
        name = name.strip()
        barcode = barcode.strip()
        if not name:
            logger.debug('пустое имя number_with_name=%s остановка', number_with_name)
            break
        quantity, *_ = specifications[-2].split()
        logger.debug('quantity=%s', quantity)
        try:
            quantity = int(quantity)
        except ValueError as e:
            logger.error('не смог преобразовать количество из строки в число - %s', e)
            no_quantity.add(f'{name} - количество: {quantity}')
            continue

        if barcode:
            to_write_off[barcode] = (name, quantity)
        else:
            no_barcode.add((name, quantity))

    logger.debug('parse_calculation закончил без ошибок')
    return to_write_off, no_barcode, no_quantity


def get_write_off_msg(write_off: dict[str, tuple[str, int]],
                      without_barcode: set[tuple[str, int]],
                      without_quantity: set[str]) -> str:
    """Формирует сообщение с продуктами, которые надо списать"""
    logger.debug('get_write_off_msg started')
    res_message = 'что надо списать:\n'
    for product, quantity in write_off.values():
        res_message += f'{product} - {quantity}шт\n'
    if without_barcode:
        res_message += '\nне могу списать, потому что нет штрих кода:\n'
        for product, quantity in without_barcode:
            res_message += f'{product} - {quantity}шт\n'
    if without_quantity:
        res_message += '\nне могу списать, потому что нет количества:\n'
        for product in without_quantity:
            res_message += f'{product}\n'

    logger.debug('get_write_off_msg finished')
    return res_message


def products_write_off(all_bifit_goods: set[Good],
                       goods_to_remove: dict[str, tuple[str, int]]) -> tuple[set[Good], set[str]]:
    """Списывает указанное в рассчете количество с товаров полученных от Бифит"""
    logger.debug('products_write_off started')
    updated_goods_set = set()
    outdated_goods_set = set()
    for scu, name_and_quantity in goods_to_remove.items():
        name, quantity = name_and_quantity
        good_str = f'{name} - штрих: {scu} - кол-во: {quantity}'
        logger.debug('ищу товар %s', good_str)
        updated_good = None
        for good in all_bifit_goods:
            if scu == good.nomenclature.barcode:
                good.goods.quantity -= quantity
                updated_good = good
                updated_goods_set.add(updated_good)
                logger.debug(f'товар нашел и сминусовал количество!')
        if updated_good is None:
            outdated_goods_set.add(good_str)
            logger.debug(f'такой товар не нашел')

    logger.debug('products_write_off finished')
    return updated_goods_set, outdated_goods_set


def goods_list_to_csv_str(products_set: set[Good]) -> str:
    """Формирует строковое представление CSV файла с обновленным количеством товаров"""
    logger.debug('начал goods_list_to_csv_str')
    headlines = ('Количество', 'Идентификатор торгового объекта', 'Идентификатор номенклатуры')
    result = ''
    csv_header = ';'.join(f'"{headline}"' for headline in headlines)
    result += csv_header + '\n'
    for product in products_set:
        csv_line = ';'.join(
            (
                f'"{product.goods.quantity}"',
                f'"{product.goods.trade_trade_object_id}"',
                f'"{product.goods.nomenclature_id}"'
            )
        )
        result += csv_line + '\n'
    logger.debug('%s', result)
    logger.debug('закончил goods_list_to_csv_str')
    return result


def send_to_yandex(ya_token: str,
                   ya_compaign_id: int,
                   ya_warehouse_id: int,
                   ya_goods_dict: dict[str:int]) -> dict:
    ya_api = YAapi(ya_token, ya_compaign_id, ya_warehouse_id, goods_dict=ya_goods_dict)
    ya_sand_remains_response = ya_api.send_remains()
    return ya_sand_remains_response


def send_to_ali(ali_token: str, ali_goods_dict: dict[str:int]) -> dict[str, str]:
    ali_api = AliApi(ali_token, ali_goods_dict)
    ali_api.fill_get_products_to_send()
    ali_sand_remains_response = ali_api.send_remains()
    return ali_sand_remains_response


def send_to_vk(vk_token: str, vk_owner_id: int, vk_api_ver: float, vk_goods_dict: dict[str:int]) -> tuple:
    vk_api = VkApi(vk_token, vk_owner_id, vk_api_ver)
    vk_products_response = VkProdResponse(vk_api.get_all_products())
    vk_products_dict = vk_products_response.get_skus_id_dict()
    vk_sand_remains_response = vk_api.send_remains(vk_products_dict, vk_goods_dict)
    return vk_sand_remains_response


def send_to_ozon(ozon_admin_key: str, ozon_client_id: str, ozon_goods_dict: dict[str:int]):
    ozon_api = OzonApi(ozon_admin_key, ozon_client_id)
    ozon_products_response = OzonProdResponse(ozon_api.get_all_products())
    ozon_products_dict = ozon_products_response.get_skus_id_dict()
    ozon_warehouses = [Warehouse(w) for w in ozon_api.get_warehouses()['result'] if w['status'] != "disabled"]
    ozon_send_remains_response = ozon_api.send_remains(ozon_products_dict, ozon_goods_dict, ozon_warehouses)
    return ozon_send_remains_response


def get_market_goods_dict(goods_set: set[Good]) -> dict[str, int]:
    return {good.nomenclature.barcode: good.goods.quantity for good in goods_set}


def get_bifit_products_set(srv_resp: dict) -> set[Good] | set[str]:
    logger.debug('начал get_bifit_products_set')
    all_prod = set()
    try:
        for item in srv_resp:
            try:
                product = Good(Goods(item['goods']), Nomenclature(item['nomenclature']))
            except KeyError as e:
                logger.error('Неожиданный ответ сервера. Ошибка формирования товара - %s', e)
                logger.debug('get_bifit_products_set завершил с ошибкой')
                return {'error', f'ошибка формирования товара. неожиданный ответ сервера - {e}'}
            else:
                all_prod.add(product)

    except TypeError as e:
        logger.error('Неожиданный ответ сервера - %s', e)
        return {'error', f'ошибка формирования списка товаров. неожиданный ответ сервера - {e}'}

    logger.debug('get_bifit_products_set закончил без ошибок')

    return all_prod


def make_ozon_write_off_items(market_prod: set[Good], ozon_posting: Posting) -> list[dict]:
    logger.debug('начал make_ozon_write_off_items')
    items = []

    for prod in ozon_posting.products:
        for good in market_prod:
            if prod.offer_id == good.nomenclature.barcode:
                item = {
                    "id": None,
                    "documentId": None,
                    "nomenclatureId": good.nomenclature.id,
                    "vendorCode": good.nomenclature.vendor_code,
                    "barcode": good.nomenclature.barcode,
                    "unitCode": good.nomenclature.unit_code,
                    "purchasePrice": good.nomenclature.purchase_price,
                    "sellingPrice": good.nomenclature.selling_price,
                    "amount": prod.quantity * good.nomenclature.purchase_price,
                    "currencyCode": None,
                    "nomenclatureFeatures": [],
                    "quantity": prod.quantity,
                    "accountBalance": good.goods.quantity
                }
                items.append(item)
                break
    logger.debug('закончил make_ozon_write_off_items')
    return items


def read_xlsx(file_path_name: str) -> Generator[Union[namedtuple, None], None, None]:
    """Генератор, читает файл построчно"""
    logger.debug('начал read_xlsx')
    required_fields = {'barcode', 'selling_price', 'purchase_price'}

    # Открываем файл
    try:
        workbook = openpyxl.load_workbook(file_path_name)
    except FileNotFoundError:
        logger.error('не нашел xlsx')
        return
    except BadZipFile:
        logger.error('этот файл не xlsx')
        return
    else:
        logger.debug('успешно загрузил xlsx')
        sheet = workbook.active

    # Получаем заголовки колонок
    headers = [cell.value for cell in sheet[1]]

    # Проверяем наличие необходимых заголовков
    missing_fields = required_fields - set(headers)

    if missing_fields:
        logger.error('Отсутствуют обязательные поля в файле - %s', missing_fields)
        return

    # Создаем namedtuple динамически
    ExcelGood = namedtuple('Good', ['barcode', 'selling_price', 'purchase_price'])

    # Получаем индексы необходимых колонок
    field_indices = {field: headers.index(field) for field in required_fields}

    # Пропускаем заголовок
    for row in sheet.iter_rows(min_row=2, values_only=True):
        # Извлекаем значения для каждого необходимого поля
        barcode = row[field_indices['barcode']]
        selling_price = row[field_indices['selling_price']]
        purchase_price = row[field_indices['purchase_price']]
        if barcode and selling_price is not None:
            # Создаем namedtuple для каждой строки
            excel_good = ExcelGood(str(barcode), selling_price, purchase_price)
            logger.debug('excel_good= %s', excel_good)
            yield excel_good


def get_barcodes_from_xlsx(file_path_name: str) -> dict[str, tuple[float, float]]:
    logger.debug('начал get_barcodes_from_xlsx')
    excel_goods = read_xlsx(file_path_name)
    return {code: (selling_price, purchase_price) for code, selling_price, purchase_price in excel_goods}


def make_price_change_items(file_name: str, bifit_prod: set[Good]) -> list[dict]:
    logger.debug('начал make_price_change_items')
    items = []

    try:
        for new_good in read_xlsx(file_name):
            logger.debug('new_good= %s', new_good)
            if new_good.barcode:
                for prod in bifit_prod:
                    if new_good.barcode == prod.nomenclature.barcode:
                        item = {
                            # "id": None,
                            # "documentId": None,
                            "nomenclatureId": prod.nomenclature.id,
                            "sellingPrice": new_good.selling_price,
                            "purchasePrice": new_good.purchase_price or 0,
                            "oldSellingPrice": prod.nomenclature.selling_price
                        }

                        logger.debug('item= %s', item)
                        items.append(item)

    except ValueError:
        logger.error('не могу получить товары из файла')

    logger.debug('закончил make_price_change_items')
    return items


def make_price_change_items_new(nomanclatures: list[Nomenclature], codes: dict):
    logger.debug('начал make_price_change_items_new')
    items = []

    for nomenclature in nomanclatures:
        item = {
            # "id": None,
            # "documentId": None,
            "nomenclatureId": nomenclature.id,
            "sellingPrice": codes[nomenclature.barcode][0],
            "purchasePrice": codes[nomenclature.barcode][1] or 0,
            "oldSellingPrice": nomenclature.selling_price
        }

        logger.debug('item= %s', item)
        items.append(item)

    logger.debug('закончил make_price_change_items_new')
    return items


def get_selling_price(product: Good) -> float:
    """
    Получает цену продажи товара из объекта товара. Если есть данные по торговым объектам,
    то берет цену первого попавшегося объекта. Если нет, то возвращает цену, указанную при создании товара.
    :param product: Объект товара Бифит-кассы
    :returns: Цена товара числом
    """
    if product.nomenclature.trade_object_relations:
        trade_objects = product.nomenclature.trade_object_relations
        prices = {obj.get('tradeObjectId'): obj.get('sellingPrice') for obj in trade_objects}
        trade_object_id = next(iter(prices))  # Заглушка, далее логика может быть изменена
        return prices.get(trade_object_id)
    return product.nomenclature.selling_price


def get_edit_product_req_params(owner_id: int,
                                api_version: float,
                                item_id: int,
                                stock_amount: int,
                                selling_price: float,
                                old_price: float) -> dict[str, int | str | float]:
    """
    Возвращает параметры запроса для изменения товара - новую цену, количество и тп.
    :param owner_id: id сообщества ВК
    :param api_version: версия api ВК
    :param item_id: id товара от ВК
    :param stock_amount: актуальное количество товара
    :param selling_price: актуальная цена товара
    :param old_price: существующая в ВК цена на данный момент
    """

    if old_price > selling_price:
        params = {
            'owner_id': owner_id,
            'v': api_version,
            'item_id': item_id,
            'stock_amount': stock_amount,
            'price': selling_price,
            'old_price': old_price
        }
    else:
        params = {
            'owner_id': owner_id,
            'v': api_version,
            'item_id': item_id,
            'stock_amount': stock_amount,
            'price': selling_price
        }
    return params


def get_vk_skus_id_dict(vk_prod: set[VkProduct]) -> dict[str:str]:
    logger.debug('формирую словарь {штрихкод: вк id}')
    d = {product.sku: product.id for product in vk_prod}
    logger.debug('количество товаров в словаре - %d', len(d))
    return d


def get_vk_skus_id_price_dict(vk_prod: set[VkProduct]) -> dict[str:(str, int)]:
    logger.debug('формирую словарь {штрихкод: вк id, вк прайс}')
    d = {product.sku: (product.id, product.price.amount) for product in vk_prod}
    logger.debug('количество товаров в словаре - %d', len(d))
    return d
