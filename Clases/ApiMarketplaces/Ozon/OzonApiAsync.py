import json

import aiohttp
from datetime import datetime, timezone, timedelta

from Clases.ApiMarketplaces.Ozon.OzonApi import OzonApi
from Clases.ApiMarketplaces.Ozon.Warehouse import Warehouse
from logger import logger


class OzonApiAsync(OzonApi):

    def __init__(self, token: str, id_: str) -> None:
        super(OzonApiAsync, self).__init__(token, id_)

    async def get_all_products_async(self) -> dict:
        logger.debug('отправляю запрос get_all_products_async в озон')
        async with aiohttp.ClientSession() as session:
            async with session.post(OzonApi.GET_ALL_PRODUCTS_URL, headers=self.headers) as response:
                logger.info(f'HTTP Request: POST {OzonApi.GET_ALL_PRODUCTS_URL}, {response.status}')
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'REQUEST ERROR {e}')
                    return {'error': f'Ошибка запроса товаров в Озон. Ответ сервера - {e}'}

                response_text = await response.text()
                logger.debug('закончил get_all_products_async в озон')
                return json.loads(response_text)

    async def send_remains_async(self, ozon_prod_dict: dict[str, str],
                                 bifit_remains: dict[str, int],
                                 warehouses: list[Warehouse]) -> dict:
        logger.debug('начал send_remains_async в озон')

        response_data = {}
        stocks = self.get_remains_list(ozon_prod_dict, bifit_remains, warehouses)

        for stock_chunk in self.chunk_stocks(stocks, 100):
            data = {"stocks": stock_chunk}
            async with aiohttp.ClientSession() as session:
                async with session.post(OzonApi.SEND_REMAINS_URL,
                                        headers=self.headers,
                                        data=json.dumps(data)) as response:
                    logger.info(f'HTTP Request: POST {OzonApi.SEND_REMAINS_URL}, {response.status}')
                    try:
                        response.raise_for_status()
                    except aiohttp.ClientResponseError as e:
                        logger.error(f'REQUEST ERROR {e}')
                        response_data.update({'error': str(e)})

                    response_json = await response.json()
                    errors = OzonApi.check_sand_remains_response(response_json)
                    if errors:
                        response_data.update(errors)
        logger.debug('закончил send_remains_async в озон')
        return response_data

    async def get_warehouses_async(self) -> dict[str, str] | dict[str, list]:
        logger.debug('начал get_warehouses_async в озон')

        async with aiohttp.ClientSession() as session:
            async with session.post(OzonApi.GET_ALL_WAREHOUSES_URL, headers=self.headers) as response:
                logger.info(f'HTTP Request: POST {OzonApi.GET_ALL_WAREHOUSES_URL}, {response.status}')
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'REQUEST get_warehouses_async ERROR {e}')
                    logger.debug('закончил get_warehouses_async в озон с ошибкой сервера')
                    return {'error': f'Ошибка запроса складов в озон - {e}'}
                logger.debug('закончил get_warehouses_async в озон успешно')
                return await response.json()

    async def get_all_postings_async(self) -> dict[str, str]:
        """метод получения всех отправлений"""
        logger.debug('начал get_all_postings_async в озон')

        T_DELTA = 7 # отрезок времени за который надо найти заказы
        dir_ = "desc"  # сортировка по убыванию
        status = 'awaiting_deliver'

        now = datetime.now(timezone.utc)
        cutoff_to = now.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
        logger.debug(f'{cutoff_to=}')
        cutoff_from = (now - timedelta(days=T_DELTA)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
        logger.debug(f'{cutoff_from=}')
        data = {
            "dir": dir_,
            "filter": {
                "cutoff_from": cutoff_from,
                "cutoff_to": cutoff_to,
                # "delivery_method_id": [],
                "is_quantum": False,
                # "provider_id": [],
                "status": status
                # "warehouse_id": []
            },
            "limit": 100,
            "offset": 0,
            "with": {
                "analytics_data": False,
                "barcodes": False,
                "financial_data": False,
                "translit": False
            }
        }
        logger.debug(f'{data=}')
        async with aiohttp.ClientSession() as session:
            async with session.post(OzonApi.GET_ALL_POSTINGS_URL,
                                    headers=self.headers,
                                    data=json.dumps(data)) as response:
                logger.info(f'HTTP Request: POST {OzonApi.GET_ALL_POSTINGS_URL}, {response.status}')
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'REQUEST get_all_postings_async ERROR {e}')
                    logger.debug('закончил get_all_postings_async в озон с ошибкой сервера')
                    return {'error': f'Ошибка запроса отправлений в озон - {e}'}

                else:
                    logger.debug('закончил get_all_postings_async в озон успешно')
                    resp_json = await response.json()
                    logger.debug('ответ сервера ozon -\n'
                                 f'{resp_json}')
                    return await response.json()

