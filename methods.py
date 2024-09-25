from Clases.ApiMarketplaces.Ali.ALIapi import AliApi
from Clases.ApiMarketplaces.Ozon.OzonApi import OzonApi
from Clases.ApiMarketplaces.Ozon.OzonProdResponse import OzonProdResponse
from Clases.ApiMarketplaces.Ozon.Warehouse import Warehouse
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


def get_markets_products(products_set: set[Good]) -> tuple[dict, dict, dict, dict]:
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
    logger.debug('parse_calculation started')
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
        *number_with_name, barcode = specifications[0].split()
        if not number_with_name:
            logger.debug(f'пустое имя {number_with_name=} остановка')
            break
        quantity, *_ = specifications[-2].split()
        logger.debug(f'{quantity=}')
        try:
            quantity = int(quantity)
        except ValueError as e:
            logger.error(f'не смог преобразовать количество из строки в число {e}')
            no_quantity.add(' '.join(number_with_name[1:]))
            continue

        if not barcode.isdigit():
            number_with_name.append(barcode)
            no_barcode.add((' '.join(number_with_name[1:]), quantity))
        else:
            product_name = ' '.join(number_with_name[1:])
            to_write_off[barcode] = (product_name, quantity)

    logger.debug('спарсил рассчтет.\n'
                 'для списания:\n'
                 f'{to_write_off}\n'
                 'без штрихкода:\n'
                 f'{no_barcode}\n'
                 'без количества:\n'
                 f'{no_quantity}')
    logger.debug('parse_calculation finished smoothly')
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
        logger.debug(f'ищу товар {good_str}')
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
    logger.debug('goods_list_to_csv_str started')
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
    logger.debug(f'{result}')
    logger.debug('goods_list_to_csv_str finished')
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
