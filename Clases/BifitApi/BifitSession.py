import json
import time
from typing import Dict

from Clases.BifitApi.Good import Good
from Clases.BifitApi.Goods import Goods
from Clases.BifitApi.GoodsListReq import GoodsListReq
from Clases.BifitApi.Nomenclature import Nomenclature
from Clases.BifitApi.OrgListReq import *
from Clases.BifitApi.Organization import *
from Clases.BifitApi.TradeObjListReq import *
from Clases.BifitApi.TradeObject import TradeObject
from Clases.BifitApi.SendCSVStocksRequest import SendCSVStocksRequest
from logger import logger


class BifitSession(Request):
    AUTH_URL = 'https://kassa.bifit.com/cashdesk-api/v1/oauth/token'

    __slots__ = (
        'username',
        'password',
        'access_token',
        'expiration_time',
        'refresh_token',
        'organisation',
        'trade_object',
    )

    def __init__(self, username, password) -> None:
        super().__init__()
        self.username = username
        self.password = password
        self.access_token = None
        self.expiration_time = None
        self.refresh_token = None
        self.organisation = None
        self.trade_object = None
        logger.debug('создал класс сессии бифит-касса')

    async def initialize(self) -> None:
        """Асинхронная инициализация класса."""
        await self.get_new_token_async()
        await self.get_first_bifit_org_async()
        await self.get_first_bifit_trade_obj_async()

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
            logger.debug('Достал время жизни токена из ответа сервера')
            self.expiration_time = time.time() + expires_in
        except (KeyError, ValueError):
            logger.error('Отсутствует или некорректное значение expires_in в ответе сервера - %s', response)

    async def get_first_bifit_org_async(self) -> None:
        """Получает первую организацию из списка Бифит-кассы (у меня она одна)"""
        logger.debug('get_first_bifit_org_async started')
        org_list_request = OrgListReq(token=await self.token)
        org_list_response = await org_list_request.send_post_async()

        if 'error' in org_list_response:
            logger.error(f'Ошибка на этапе запроса списка организаций - {org_list_response}')
        else:
            try:
                org_list = [Organization(org) for org in org_list_response]
                self.organisation = org_list[0]
                logger.debug('get_bifit_org_list_async finished smoothly')
            except KeyError as e:
                logger.error(f'Ошибка формирования списка организаций - {e}')
                logger.debug('get_bifit_org_list_async finished with exception')

    async def get_first_bifit_trade_obj_async(self) -> None:
        """Получает первый торговый объект из списка Бифит-кассы (у меня он один)"""
        logger.debug('get_first_bifit_trade_obj_async started')
        if self.organisation is None:
            await self.get_first_bifit_org_async()
        trade_obj_list_request = TradeObjListReq(token=await self.token, org_id=self.organisation.id)
        trade_obj_list_response = await trade_obj_list_request.send_post_async()

        if 'error' in trade_obj_list_response:
            logger.error(f'Ошибка на этапе запроса списка организаций - {trade_obj_list_response}')
        else:
            try:
                trade_obj_list = [TradeObject(obj) for obj in trade_obj_list_response]
                self.trade_object = trade_obj_list[0]
                logger.debug('get_bifit_org_list_async finished smoothly')
            except KeyError as e:
                logger.error(f'Ошибка формирования списка торговых объектов - {e}')
                logger.debug('get_bifit_org_list_async finished with exception')

    async def get_bifit_products_set_async(self) -> set[Good] | None:
        """получает список всех товаров из склада Бифит-кассы"""
        logger.debug('get_bifit_products_set_async started')

        token = await self.token
        org = await self.org
        trade_obj = await self.trade_obj

        goods_list_request = GoodsListReq(
            token=token,
            org_id=org.id,
            trade_obj_id=trade_obj.id
        )
        goods_list_response = await goods_list_request.send_post_async()
        if 'error' in goods_list_response:
            logger.error(f'Ошибка на этапе запроса списка товаров - {goods_list_response}')
            return None
        try:
            products = {Good(Goods(item['goods']), Nomenclature(item['nomenclature'])) for item in goods_list_response}
            logger.debug('get_bifit_products_set_async finished smoothly')
            return products
        except KeyError as e:
            logger.error(f'Ошибка формирования множества товаров - {e}')
            logger.debug('get_bifit_products_set_async finished with exception')
            return None

    async def send_csv_stocks(self, stocks_csv_str: str) -> dict[str, str] | None:
        """Отправляет CSV строку с остатками"""
        logger.debug('send_stocks started')

        token = await self.token
        org = await self.org

        send_stocks_request = SendCSVStocksRequest(
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
