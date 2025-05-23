import asyncio
import time
from datetime import datetime, timezone, timedelta

from Clases.BifitApi.Contactor import Contactor
from Clases.BifitApi.ContactorsRequest import ContactorsRequest
from Clases.BifitApi.ExecutePriceChangeRequest import ExecutePriceChangeRequest
from Clases.BifitApi.GetNomenclaturesRequest import GetNomenclaturesRequest
from Clases.BifitApi.MakePriceChangeRequest import MakePriceChangeRequest
from Clases.BifitApi.MakeWriteOffDocRequest import MakeWriteOffDocRequest
from Clases.BifitApi.ParentNomenclaturesReq import ParentNomenclaturesReq
from Clases.BifitApi.SendCSVStocksRequest import SendCSVStocksRequest
from Exceptions.ResponseContentException import ResponseContentException
from Exceptions.ResponseStatusException import ResponseStatusException
from methods.sync_methods import *
from methods.methods_async import get_pic_url


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
    MAKE_PRICE_CHANGE_DOCS_URL = f'{BIFIT_API_URL}/protected/price_change'
    GET_NOMENCLATURES_BY_BARCODES_URL = f'{BIFIT_API_URL}/protected/nomenclatures/barcodes/list/read'

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
        self.organisation: Organization | None = None
        self.trade_object: TradeObject | None = None
        self.yml_str: str | None = None
        logger.debug('создал класс сессии бифит-касса')

    async def initialize(self) -> None:
        """Асинхронная инициализация класса."""
        logger.debug('инициализирую сессию Бифит')
        await self.get_new_token_async()
        await self.get_first_bifit_org_async()
        await self.get_first_bifit_trade_obj_async()
        await self.get_yml_async()
        logger.debug('инициализацию закончил')

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
            logger.debug('нашел данные по организации в экземпляре класса сессии')
        return self.organisation

    @property
    async def trade_obj(self) -> TradeObject:
        """Получение торгового объекта из состояния экземпляра класса"""
        logger.debug('trade_obj started')
        if self.trade_object is None:
            logger.debug('в сессии нет данных по торговому объекту, пробую получить')
            await self.get_first_bifit_trade_obj_async()
        else:
            logger.debug('нашел данные по торговому объекту в экземпляре класса сессии')
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
        logger.debug('начал get_first_bifit_trade_obj_async')
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

    async def get_all_bifit_prod_response(self) -> dict:
        """Получает список ответ сервера на запрос всех товаров из склада Бифит-кассы"""
        logger.debug('начал get_all_bifit_prod')
        # Получение токена и других необходимых данных
        token = await self.token
        org = await self.org
        trade_obj = await self.trade_obj

        goods_list_request = GoodsListReq(
            url=BifitSession.GOODS_LIST_URL,
            token=token,
            org_id=org.id,
            trade_obj_id=trade_obj.id
        )

        logger.debug('Отправляю запрос на получение всех товаров склада Бифит-кассы')
        return await goods_list_request.send_post_async()

    async def get_all_bifit_prod(self) -> set[Good] | set[str]:
        """Получает множество всех товаров из склада Бифит-кассы"""
        logger.debug('начал get_all_bifit_prod')
        # Получение токена и других необходимых данных
        token = await self.token
        org = await self.org
        trade_obj = await self.trade_obj

        goods_list_request = GoodsListReq(
            url=BifitSession.GOODS_LIST_URL,
            token=token,
            org_id=org.id,
            trade_obj_id=trade_obj.id
        )

        logger.debug('Отправляю запрос на получение всех товаров склада Бифит-кассы')
        goods_list_response = await goods_list_request.send_post_async()

        return get_bifit_products_set(goods_list_response)

    async def get_bifit_prod_by_marker(self, markers: tuple[str]) -> dict[str, str] | dict[str, set]:
        logger.debug('начал get_bifit_prod_by_marker')
        srv_resp = await self.get_all_bifit_prod_response()
        if 'error' in srv_resp:
            return {'error': f'{srv_resp[1]}'}

        market_products: dict = {}

        for item in srv_resp:
            try:
                product = Good(Goods(item['goods']), Nomenclature(item['nomenclature']))
            except KeyError as e:
                logger.error(f'Неожиданный ответ сервера. Ошибка формирования товара - {e}')
                logger.debug('get_bifit_products_set_async finished with exception')
                return {'error': f'ошибка формирования товара. неожиданный ответ сервера - {e}'}
            else:
                try:
                    markets: list[str] = product.nomenclature.vendor_code.split("-")
                except AttributeError:
                    continue
                else:
                    for marker in markers:
                        if marker in markets:

                            if marker not in market_products:
                                market_products[marker] = set()
                            market_products[marker].add(product)

        return market_products

    async def get_bifit_nomenclatures_by_barcode(self, codes: list[str]) -> list[Nomenclature] | None:
        """Получает множество всех номенклатур по штрихкодам из склада Бифит-кассы"""
        logger.debug('начал get_bifit_nomenclatures_by_barcode')

        # Получение токена и других необходимых данных
        token = await self.token
        org = await self.org

        nomenclatures_request = GetNomenclaturesRequest(
            url=BifitSession.GET_NOMENCLATURES_BY_BARCODES_URL,
            token=token,
            org_id=org.id,
            barcodes=codes
        )
        logger.debug('Отправляю запрос на получение номенклатур по штрихкодам')
        nomenclatures_response = await nomenclatures_request.send_post_async()

        if 'error' in nomenclatures_response:
            logger.error('Ошибка на этапе запроса номенклатур - %s', nomenclatures_response)
            return None

        logger.debug('номенклатуры получил. пробую прочитать')

        try:
            nomenclatures_lst = [Nomenclature(item) for item in nomenclatures_response]
        except TypeError as e:
            logger.error('TypeError Неожиданный ответ сервера - %s', e)
            return None
        except KeyError as e:
            logger.error('KeyError Неожиданный ответ сервера - %s', e)
            return None
        return nomenclatures_lst

    async def get_bifit_prod_by_markers(self, markers: tuple[str] = ()) -> dict[str, str] | set[Good]:
        """НЕ ИСПОЛЬЗУЕТСЯ! Получает список всех товаров из склада Бифит-кассы по маркерам"""
        logger.debug('начал get_bifit_prod_by_markers')

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
            return goods_list_response

        logger.debug('товары получил. пробую прочитать')

        try:
            for item in goods_list_response:
                try:
                    product = Good(Goods(item['goods']), Nomenclature(item['nomenclature']))
                except KeyError as e:
                    logger.error(f'Неожиданный ответ сервера. Ошибка формирования товара - {e}')
                    logger.debug('get_bifit_products_set_async finished with exception')
                    return {'error': f'{e}'}

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
            return {'error': f'{e}'}

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
            parent_noms_list = tuple(Nomenclature(item_) for item_ in parent_noms_response)
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

        for good_ in goods_list:
            coroutines.add(self.get_parent_nomenclature_async(good_.nomenclature.id))

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

        for good_ in goods_list:
            coroutines.append(self.get_parent_nomenclature_async(good_.nomenclature.id))

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
            return {good_: parent_nomenclature for good_, parent_nomenclature in zip(goods_list, parent_nomenclatures)}

    async def get_yab_goods_list(self, goods_set: set[Good]) -> list[dict]:
        """Формирует отсортированный по дате изменения список словарей
        {'good': Товар, 'parent_nomenclature': Родительская номенклатура, 'vendor': Поставщик}"""
        vendor_ids = list({product.nomenclature.contractor_id for product in goods_set})
        coroutines_nomenclatures = [self.get_parent_nomenclature_async(good_.nomenclature.id) for good_ in goods_set]

        try:
            vendors_dict = await self.get_vendors_async(vendor_ids)
            logger.debug('получил словарь {"id поставщика": Поставщик}\n' f'{vendors_dict=}')
            parent_nomenclatures = await asyncio.gather(*coroutines_nomenclatures)
            logger.debug(f'{parent_nomenclatures=}')
        except (ResponseContentException, ResponseStatusException) as e:
            logger.debug(f'неожиданный ответ сервера {e} не могу сформировать список номенклатур и поставщиков')
            return []

        yab_goods_list = []

        sorted_yab_goods = sorted(list(zip(goods_set, parent_nomenclatures)),
                                  key=lambda item: item[0].nomenclature.changed)

        for good_, parent_nomenclature in sorted_yab_goods:
            vendor = vendors_dict.get(good_.nomenclature.contractor_id)
            yab_goods_list.append({'good': good_, 'parent_nomenclature': parent_nomenclature, 'vendor': vendor})

        return yab_goods_list

    async def get_yml_async(self) -> dict:
        logger.debug(f'начал get_yml_async')

        my_site_url = 'https://pronogti.store'

        tz = timezone(timedelta(hours=3))
        current_time = datetime.now(tz)
        products_response = await self.get_bifit_prod_by_marker(('yab',))

        yab_goods_set = products_response.get('yab')

        if isinstance(yab_goods_set, set):
            yab_products_list = await self.get_yab_goods_list(yab_goods_set)
        else:
            logger.debug(f'get_yml закончен с ошибкой')
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
            description = product.nomenclature.description

            if description is None:
                logger.error('Забыл указать описание')
                logger.debug('для товара %s Забыл указать описание', product)
                errors[product.nomenclature.name] = 'Забыл указать описание'

            categories.add(category)

            if vendor is None:
                logger.error('Забыл указать производителя')
                errors[product.nomenclature.name] = 'Забыл указать производителя'
                vendor = Contactor({'shortName': 'n0 vendor'})
                logger.debug('для товара %s Забыл указать производителя', product)
                pic_url = f'{my_site_url}/images/no-image.jpg'
            else:
                pic_url = await get_pic_url(product.nomenclature.short_name, vendor.short_name)
                if pic_url == f'{my_site_url}/images/no-image.jpg':
                    logger.error('Не нашел картинку на сервере')
                    logger.debug('для товара %s Не нашел картинку на сервере', product)
                    errors[product.nomenclature.name] = 'Не нашел картинку на сервере'

            offer_id = product.nomenclature.barcode or product.nomenclature.id

            offers_content += f"""<offer id="{offer_id}"  available="{available}">
                        <name>{product.nomenclature.name}</name>
                        <vendor>{vendor.short_name}</vendor>
                        <price>{get_selling_price(product)}</price>
                        <currencyId>RUR</currencyId>
                        <categoryId>{category.id}</categoryId>
                        <picture>{pic_url}</picture>
                        <description>
                            <![CDATA[
                                {description}
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
        logger.debug(f'закончил get_yml')
        return errors

    async def make_ozon_write_off_doc_async(
            self,
            ozon_products: set[Good],
            ozon_postings: list[Posting],
            execute: bool = False  # нужно ли проводить документ
    ) -> list[dict]:
        logger.debug(f'начал make_ozon_write_off_doc_async')
        coroutines = set()

        url = BifitSession.BIFIT_API_URL
        token = await self.token
        org = await self.org
        trade_obj = await self.trade_obj
        params = {'execute': str(execute)}

        for posting in ozon_postings:
            posting_items = make_ozon_write_off_items(ozon_products, posting)

            write_off_doc_req = MakeWriteOffDocRequest(url=url,
                                                       token=token,
                                                       org_id=org.id,
                                                       trade_obj_id=trade_obj.id,
                                                       doc_num=f'ozon {posting.posting_number}',
                                                       items=posting_items,
                                                       params=params)
            coroutines.add(write_off_doc_req.send_post_async())

        return await asyncio.gather(*coroutines)

    async def make_price_change_docs_async(self,
                                           nomenclatures: list[Nomenclature],
                                           barcodes: dict) -> dict | int:
        logger.debug(f'начал make_price_change_docs_async')

        url = BifitSession.MAKE_PRICE_CHANGE_DOCS_URL
        token = await self.token
        org = await self.org
        trade_obj = await self.trade_obj
        change_items = make_price_change_items_new(nomenclatures, barcodes)

        change_price_req = MakePriceChangeRequest(url=url,
                                                  token=token,
                                                  org_id=org.id,
                                                  trade_obj_id=trade_obj.id,
                                                  items=change_items)

        response = await change_price_req.send_post_async()

        if isinstance(response, dict):
            return -1

        return response

    async def execute_price_change_docs(self, doc_ids: list[int]):
        logger.debug(f'начал execute_price_change_docs')

        url = BifitSession.BIFIT_API_URL
        token = await self.token
        org = await self.org

        execute_docs_req = ExecutePriceChangeRequest(url=url,
                                                     token=token,
                                                     org_id=org.id,
                                                     doc_ids=doc_ids)

        return await execute_docs_req.send_post_async()
