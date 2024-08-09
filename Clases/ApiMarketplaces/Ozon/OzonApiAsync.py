import json

import aiohttp

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
                        response_data.append({'error': str(e)})

                    response_json = await response.json()
                    errors = OzonApi.check_sand_remains_response(response_json)
                    if errors:
                        response_data.update(errors)
        logger.debug('закончил send_remains_async в озон')
        return response_data

    async def get_warehouses_async(self) -> dict[str, str] | dict[str, list]:
        logger.debug('начал get_warehouses_async в озон')

        async with aiohttp.ClientSession() as session:
            async with session.post(OzonApi.GET_ALL_WAREHOUSES, headers=self.headers) as response:
                logger.info(f'HTTP Request: POST {OzonApi.GET_ALL_WAREHOUSES}, {response.status}')
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'REQUEST get_warehouses_async ERROR {e}')
                    logger.debug('закончил get_warehouses_async в озон с ошибкой сервера')
                    return {'error': f'Ошибка запроса складов в озон - {e}'}
                logger.debug('закончил get_warehouses_async в озон успешно')
                return await response.json()
