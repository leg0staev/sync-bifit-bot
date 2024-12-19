import asyncio
import time
from datetime import datetime, timezone, timedelta

from Clases.BifitApi.Contactor import Contactor
from Clases.BifitApi.ContactorsRequest import ContactorsRequest
from Clases.BifitApi.Good import Good
from Clases.BifitApi.Goods import Goods
from Clases.BifitApi.GoodsListReq import GoodsListReq
from Clases.BifitApi.Nomenclature import Nomenclature
from Clases.BifitApi.OrgListReq import *
from Clases.BifitApi.Organization import *
from Clases.BifitApi.ParentNomenclaturesReq import *
from Clases.BifitApi.SendCSVStocksRequest import SendCSVStocksRequest
from Clases.BifitApi.TradeObjListReq import *
from Clases.BifitApi.TradeObject import TradeObject
from Exceptions.ResponseContentException import ResponseContentException
from Exceptions.ResponseStatusException import ResponseStatusException
from logger import logger
from methods_async import get_pic_url


class BifitSession(Request):
    BIFIT_API_URL = 'https://kassa.bifit.com/cashdesk-api/v1'
    AUTH_URL = f'{BIFIT_API_URL}/oauth/token'
    ORG_LIST_URL = f'{BIFIT_API_URL}/protected/organizations/list/read_all'
    TRADE_OBJ_LIST_URL = f'{BIFIT_API_URL}/protected/trade_objects/list/read_all'
    GOODS_LIST_URL = f'{BIFIT_API_URL}/protected/goods/list/read'
    GOODS_QUANTITY_URL = f'{BIFIT_API_URL}/protected/goods/quantity'
    SEND_CSV_URL = f'{BIFIT_API_URL}/protected/goods/csv/upload'
    PARENT_NOM_URL = f'{BIFIT_API_URL}/protected/nomenclatures'
    CONTACTORS_URL = f'{BIFIT_API_URL}/protected/contractors/list'

    __slots__ = (
        'username',
        'password',
        'access_token',
        'expiration_time',
        'refresh_token',
        'organisation',
        'trade_object',
        'yml_str',
    )

    def __init__(self, username: str, password: str) -> None:
        super().__init__()
        self.username: str = username
        self.password: str = password
        self.access_token: str | None = None
        self.expiration_time: float | None = None
        self.refresh_token: str | None = None
        self.organisation: str | None = None
        self.trade_object: str | None = None
        self.yml_str: str | None = None
        logger.debug('создал класс сессии бифит-касса')

    async def initialize(self) -> None:
        """Асинхронная инициализация класса."""
        logger.debug('инициализирую сессию Бифит')
        await self.get_new_token_async()
        await self.get_first_bifit_org_async()
        await self.get_first_bifit_trade_obj_async()
        await self.get_yml_async()

    @property
    async def token(self) -> str:
        """Получение токена из состояния экземпляра класса"""
        logger.debug('token started')
        if self.expiration_time is None:
            logger.debug('старого токена нет, пробую получить')
            await self.get_new_token_async()
        elif self.expiration_time < time.time():
            logger.debug('старый токен истек, пробую получить новый')
            await self.get_token_by_refresh_async()
        else:
            logger.debug('токен существует и он еще не истек')
        return self.access_token

    @property
    async def org(self) -> Organization:
        """Получение организации из состояния экземпляра класса"""
        logger.debug('organisation started')
        if self.organisation is None:
            logger.debug('в сессии нет данных по организации, пробую получить')
            await self.get_first_bifit_org_async()
        else:
            logger.debug('нашел данные по торговому объекту в экземпляре класса сессии')
        return self.organisation

    @property
    async def trade_obj(self) -> TradeObject:
        """Получение торгового объекта из состояния экземпляра класса"""
        logger.debug('trade_obj started')
        if self.trade_object is None:
            logger.debug('в сессии нет данных по торговому объекту, пробую получить')
            await self.get_first_bifit_trade_obj_async()
        else:
            logger.debug('нашел данные по организации в экземпляре класса сессии')
        return self.trade_object

    async def get_token_by_refresh_async(self) -> None:
        """Получение токена, если он истек."""
        logger.debug('get_token_by_refresh_async started')
        body = {
            "refresh_token": self.refresh_token,
            "client_id": "cashdesk-rest-client",
            "client_secret": "cashdesk-rest-client",
            "grant_type": "refresh_token",
        }
        response = await self.send_post_async(url=BifitSession.AUTH_URL, json_data=body)
        self.bifit_token_response_parse(response)

    async def get_new_token_async(self) -> None:
        """Получение токена, если он отсутствует."""
        logger.debug('get_token_async started')
        body = {
            "username": self.username,
            "password": self.password,
            "client_id": "cashdesk-rest-client",
            "client_secret": "cashdesk-rest-client",
            "grant_type": "password",
        }
        response = await self.send_post_async(url=BifitSession.AUTH_URL, json_data=body)
        # logger.debug(f'ответ сервера - {response}')
        self.bifit_token_response_parse(response)

    def bifit_token_response_parse(self, response: dict) -> None:
        """Парсинг ответа на запрос токена."""
        try:
            self.access_token = response['access_token']
            logger.debug('Достал токен из ответа сервера')
        except KeyError:
            logger.error('Отсутствует access_token в ответе сервера - %s', response)

        try:
            self.refresh_token = response['refresh_token']
            logger.debug('Достал рефреш токен из ответа сервера')
        except KeyError:
            logger.error('Отсутствует refresh_token в ответе сервера - %s', response)

        try:
            expires_in = float(response['expires_in'])
        except (KeyError, ValueError):
            logger.error('Отсутствует или некорректное значение expires_in в ответе сервера - %s', response)
        else:
            logger.debug('Достал время жизни токена из ответа сервера')
            self.expiration_time = time.time() + expires_in

    async def get_first_bifit_org_async(self) -> None:
        """Получает первую организацию из списка Бифит-кассы (у меня она одна)"""
        logger.debug('get_first_bifit_org_async started')
        org_list_request = OrgListReq(url=BifitSession.ORG_LIST_URL, token=await self.token)
        org_list_response = await org_list_request.send_post_async()

        if 'error' in org_list_response:
            logger.error(f'Ошибка на этапе запроса списка организаций - {org_list_response}')
        else:
            try:
                org_list = [Organization(org) for org in org_list_response]
            except KeyError as e:
                logger.error(f'Ошибка формирования списка организаций - {e}')
                logger.debug('get_bifit_org_list_async finished with exception')
            else:
                self.organisation = org_list[0]
                logger.debug('get_bifit_org_list_async finished smoothly')

    async def get_first_bifit_trade_obj_async(self) -> None:
        """Получает первый торговый объект из списка Бифит-кассы (у меня он один)"""
        logger.debug('get_first_bifit_trade_obj_async started')
        if self.organisation is None:
            await self.get_first_bifit_org_async()
        trade_obj_list_request = TradeObjListReq(
            url=BifitSession.TRADE_OBJ_LIST_URL,
            token=await self.token,
            org_id=self.organisation.id
        )
        trade_obj_list_response = await trade_obj_list_request.send_post_async()

        if 'error' in trade_obj_list_response:
            logger.error(f'Ошибка на этапе запроса списка организаций - {trade_obj_list_response}')
        else:
            try:
                trade_obj_list = [TradeObject(obj) for obj in trade_obj_list_response]
            except KeyError as e:
                logger.error(f'Ошибка формирования списка торговых объектов - {e}')
                logger.debug('get_bifit_org_list_async finished with exception')
            else:
                self.trade_object = trade_obj_list[0]
                logger.debug('get_bifit_org_list_async finished smoothly')

    async def get_bifit_products_async(self) -> tuple[dict, dict, dict, dict, list, set]:
        """Получает список всех товаров из склада Бифит-кассы"""
        logger.debug('get_bifit_products_set_async started')

        token = await self.token
        org = await self.org
        trade_obj = await self.trade_obj

        products: set[Good] = set()
        ya_goods: dict[str:int] = {}
        ali_goods: dict[str:int] = {}
        vk_goods: dict[str:int] = {}
        ozon_goods: dict[str:int] = {}
        yab_goods: list[Good] = []

        goods_list_request = GoodsListReq(
            url=BifitSession.GOODS_LIST_URL,
            token=token,
            org_id=org.id,
            trade_obj_id=trade_obj.id
        )
        logger.debug('отправляю запрос на получение всех товаров склада  Бифит кассы')
        goods_list_response = await goods_list_request.send_post_async()

        if 'error' in goods_list_response:
            logger.error(f'Ошибка на этапе запроса списка товаров - {goods_list_response}')
            raise ResponseStatusException(goods_list_response.get('error'))
        try:
            for item in goods_list_response:
                product = Good(Goods(item['goods']), Nomenclature(item['nomenclature']))
                products.add(product)
                try:
                    markets: list[str] = product.nomenclature.vendor_code.split("-")
                except AttributeError:
                    # print(f"Ошибка: товар {product.get_name()}")
                    continue
                else:
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
                    if "yab" in markets:
                        yab_goods.append(product)

            logger.debug('get_bifit_products_set_async finished smoothly')
            return ya_goods, ali_goods, vk_goods, ozon_goods, yab_goods, products
        except KeyError as e:
            logger.error(f'Ошибка формирования множества товаров - {e}')
            logger.debug('get_bifit_products_set_async finished with exception')
            raise ResponseContentException(goods_list_response)

    async def get_bifit_prod_by_markers(self, markers: tuple[str] = ()) -> None | set[Good] | dict[str, dict[str, int]]:
        """Получает список всех товаров из склада Бифит-кассы по маркерам"""
        logger.debug('get_bifit_prod_by_markers started')

        # Получение токена и других необходимых данных
        token = await self.token
        org = await self.org
        trade_obj = await self.trade_obj

        all_products: set[Good] = set()
        market_products: dict = {}

        goods_list_request = GoodsListReq(
            url=BifitSession.GOODS_LIST_URL,
            token=token,
            org_id=org.id,
            trade_obj_id=trade_obj.id
        )

        logger.debug('Отправляю запрос на получение всех товаров склада Бифит-кассы')
        goods_list_response = await goods_list_request.send_post_async()

        if 'error' in goods_list_response:
            logger.error(f'Ошибка на этапе запроса списка товаров - {goods_list_response}')
            return None

        logger.debug('товары получил. пробую прочитать')

        try:
            for item in goods_list_response:
                try:
                    product = Good(Goods(item['goods']), Nomenclature(item['nomenclature']))
                except KeyError as e:
                    logger.error(f'Неожиданный ответ сервера. Ошибка формирования товара - {e}')
                    logger.debug('get_bifit_products_set_async finished with exception')
                    return None

                if markers:
                    for marker in markers:
                        try:
                            markets: list[str] = product.nomenclature.vendor_code.split("-")
                        except AttributeError:
                            continue

                        if marker in markets:
                            if marker == 'yab':
                                if marker not in market_products:
                                    market_products[marker] = set()
                                market_products[marker].add(product)
                            else:
                                if marker not in market_products:
                                    market_products[marker] = {}
                                market_products[marker][product.nomenclature.barcode] = product.goods.quantity
                else:
                    all_products.add(product)

        except TypeError as e:
            logger.error(f'Неожиданный ответ сервера - {e}')
            return None

        logger.debug('get_bifit_prod_by_markers finished smoothly')
        return all_products or market_products

    async def send_csv_stocks(self, stocks_csv_str: str) -> dict[str, str] | None:
        """Отправляет CSV строку с остатками"""
        logger.debug('send_stocks started')

        token = await self.token
        org = await self.org

        send_stocks_request = SendCSVStocksRequest(
            url=BifitSession.SEND_CSV_URL,
            token=token,
            org_id=org.id,
            csv_str=stocks_csv_str
        )
        logger.debug('сформировал класс запроса на отправку CSV. Отправляю запрос')

        send_stocks_response = await send_stocks_request.send_post_async()
        logger.debug(f'ответ сервера {send_stocks_response}')
        # {'exceptionMessage': None, 'exceptionList': [], 'itemQty': 1, 'consumedTime': 0}

        if 'error' in send_stocks_response:
            logger.error(f'Ошибка на этапе отправки списка товаров - {send_stocks_response}')
            logger.debug('send_stocks finished with exception')
            return None

        logger.debug('send_stocks finished')
        return send_stocks_response

    async def get_parent_nomenclature_async(self, nomenclature_id) -> Nomenclature | None:
        logger.debug('get_parent_nomenclatures_async started')
        token = await self.token
        parent_noms_request = ParentNomenclaturesReq(
            url=BifitSession.PARENT_NOM_URL,
            token=token,
            nomenclature_id=nomenclature_id
        )
        logger.debug(
            f'сформировал класс запроса родительских номенклатур для товара c id {nomenclature_id}. '
            f'Отправляю запрос')

        parent_noms_response = await parent_noms_request.send_get_async()
        if 'error' in parent_noms_response:
            logger.error(f'Ошибка на этапе запроса родительских номенклатур - {parent_noms_response}')
            logger.debug('send_stocks finished with exception')
            raise ResponseStatusException(parent_noms_response.get('error'))
        try:
            parent_noms_list = tuple(Nomenclature(item) for item in parent_noms_response)
        except KeyError as e:
            logger.error(f'Ошибка формирования родительских номенклатур.'
                         f'неожиданный ответ от сервера - {e}')
            logger.debug('get_bifit_products_set_async finished with exception')
            raise ResponseContentException(parent_noms_response)
        else:
            logger.debug('get_parent_nomenclatures_async finished smoothly')
            return parent_noms_list[1]

    async def get_vendors_async(self, vendors_id: list[int]):
        """Формирует словарь {'id поставщика': Поставщик}"""
        logger.debug('get_vendor_async started')
        token = await self.token
        org = await self.org

        contactors_dict = {}

        contactors_list_request = ContactorsRequest(
            url=self.CONTACTORS_URL,
            token=token,
            org_id=org.id,
            contactors_ids=vendors_id,
        )
        logger.debug(f'сформировал класс запроса поставщиков. Отправляю запрос')

        contactors_list_response = await contactors_list_request.send_post_async()

        if 'error' in contactors_list_response:
            logger.error(f'Ошибка на этапе запроса поставщиков - {contactors_list_response}')
            logger.debug('send_stocks finished with exception')
            raise ResponseStatusException(contactors_list_response.get('error'))

        try:
            for item in contactors_list_response:
                # item = json.loads(item)
                contactors_dict[item.get("id")] = Contactor(item)
        except KeyError as e:
            logger.error(f'Ошибка формирования перечня поставщиков.'
                         f'неожиданный ответ от сервера - {e}')
            logger.debug('get_vendor_async finished with exception')
            raise ResponseContentException(contactors_list_response)
        else:
            logger.debug('get_vendor_async finished smoothly')
            return contactors_dict

    async def get_yab_categories_dict(self, goods_list: list[Good]) -> dict[str, int]:
        """Формирует словарь {'имя категории': id категории}"""
        logger.debug('get_yab_categories_dict started')
        coroutines = set()
        categories = dict()

        for good in goods_list:
            coroutines.add(self.get_parent_nomenclature_async(good.nomenclature.id))

        try:
            parent_nomenclatures = await asyncio.gather(*coroutines)
        except ResponseContentException as e:
            logger.debug(f'неожиданный ответ сервера {e} '
                         f'не могу сформировать список номенклатур')
            return categories
        except ResponseStatusException as e:
            logger.debug(f'плохой статус код {e} ')
            return categories
        else:
            logger.debug(f'{parent_nomenclatures=}')

            for parent_nomenclature in parent_nomenclatures:
                categories[parent_nomenclature.name] = parent_nomenclature.id
            logger.debug('get_yab_categories_dict finished smoothly')
            return categories

    async def get_yab_goods_old(self, goods_list: list[Good]) -> dict[Good, Nomenclature]:
        """Формирует словарь {Товар: Родительская номенклатура}"""

        coroutines = list()

        for good in goods_list:
            coroutines.append(self.get_parent_nomenclature_async(good.nomenclature.id))

        try:
            parent_nomenclatures = await asyncio.gather(*coroutines)
        except ResponseContentException as e:
            logger.debug(f'неожиданный ответ сервера {e} '
                         f'не могу сформировать список номенклатур')
            return {}
        except ResponseStatusException as e:
            logger.debug(f'плохой статус код {e} ')
            return {}
        else:
            logger.debug(f'{parent_nomenclatures=}')
            return {good: parent_nomenclature for good, parent_nomenclature in zip(goods_list, parent_nomenclatures)}

    async def get_yab_goods(self, goods_set: set[Good]) -> list[dict]:
        """Формирует отсортированный по дате изменения список словарей
        {'good': Товар, 'parent_nomenclature': Родительская номенклатура, 'vendor': Поставщик}"""
        vendor_ids = list({product.nomenclature.contractor_id for product in goods_set})
        coroutines_nomenclatures = [self.get_parent_nomenclature_async(good.nomenclature.id) for good in goods_set]

        try:
            vendors_dict = await self.get_vendors_async(vendor_ids)
            logger.debug('получил словарь {"id поставщика": Поставщик}\n' f'{vendors_dict=}')
            parent_nomenclatures = await asyncio.gather(*coroutines_nomenclatures)
            logger.debug(f'{parent_nomenclatures=}')
        except (ResponseContentException, ResponseStatusException) as e:
            logger.debug(f'неожиданный ответ сервера {e} не могу сформировать список номенклатур и поставщиков')
            return []

        yab_goods_dict = []

        sorted_yab_goods = sorted(list(zip(goods_set, parent_nomenclatures)),
                                  key=lambda item: item[0].nomenclature.changed)

        for good, parent_nomenclature in sorted_yab_goods:
            vendor = vendors_dict.get(good.nomenclature.contractor_id)
            yab_goods_dict.append({'good': good, 'parent_nomenclature': parent_nomenclature, 'vendor': vendor})

        return yab_goods_dict

    async def get_yml_async(self) -> dict:
        logger.debug(f'get_yml_async started')

        my_site_url = 'https://pronogti.store'

        tz = timezone(timedelta(hours=3))
        current_time = datetime.now(tz)
        products_response = await self.get_bifit_prod_by_markers(('yab',))
        if isinstance(products_response, dict):
            yab_products_list = await self.get_yab_goods(products_response.get('yab'))
        else:
            logger.debug(f'get_yml finished with error')
            return {}

        categories_content = ''
        offers_content = ''
        errors = {}

        categories = set()

        for item in yab_products_list:
            product = item.get('good')

            if product.goods.quantity == 0:
                continue

            available = 'true'
            # available = 'true' if product.goods.quantity > 0 else 'false'

            vendor = item.get('vendor')
            category = item.get('parent_nomenclature')

            categories.add(category)

            if vendor is None:
                errors[product.nomenclature.name] = 'Забыл указать производителя'
                vendor = Contactor({'shortName': 'n0 vendor'})
                logger.debug(f'для товара {product} Забыл указать производителя')
                pic_url = f'{my_site_url}/images/no-image.jpg'
            else:
                pic_url = await get_pic_url(product.nomenclature.short_name, vendor.short_name)
                if pic_url == f'{my_site_url}/images/no-image.jpg':
                    logger.debug(f'для товара {product} Не нашел картинку на сервере')
                    errors[product.nomenclature.name] = 'Не нашел картинку на сервере'

            offer_id = product.nomenclature.barcode or product.nomenclature.id

            offers_content += f"""<offer id="{offer_id}"  available="{available}">
                        <name>{product.nomenclature.name}</name>
                        <vendor>{vendor.short_name}</vendor>
                        <price>{product.nomenclature.selling_price}</price>
                        <currencyId>RUR</currencyId>
                        <categoryId>{category.id}</categoryId>
                        <picture>{pic_url}</picture>
                        <description>
                            <![CDATA[
                                {product.nomenclature.description}
                            ]]>
                        </description>
                    </offer>"""
        for category in categories:
            categories_content += f'<category id="{category.id}">{category.name}</category>\n'

        self.yml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
    <yml_catalog date="{current_time.isoformat()}">
        <shop>
            <name>pronogti.store</name>
            <company>pronogti.store</company>
            <url>https://pronogti.store</url>
            <currencies>
                <currency id="RUR" rate="1"/>
            </currencies>
            <categories>
                {categories_content.strip()}
            </categories>
            <offers>
                {offers_content}
            </offers>
        </shop>
    </yml_catalog>
"""
        logger.debug(f'get_yml finished')
        return errors
