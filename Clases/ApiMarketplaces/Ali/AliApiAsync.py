import asyncio
import json
from typing import Dict

import aiohttp

from Clases.ApiMarketplaces.Ali.ALIapi import AliApi
from Clases.ApiMarketplaces.Ali.AliProduct import AliProduct
from Clases.BifitApi.Good import Good
from logger import logger


class AliApiAsync(AliApi):

    def __init__(self,
                 token: str,
                 products_dict: dict[str, int] = None,
                 product_set: set[Good] = None) -> None:
        super(AliApiAsync, self).__init__(token, products_dict, product_set)

    async def fill_get_products_to_send(self):
        logger.debug('fill_get_products_to_send (AliApiAsync) started')
        response = await self.search_by_sku_async()
        try:
            products = [AliProduct(p) for p in response['data']]
        except (KeyError, TypeError) as e:
            logger.error("Ошибка в ответе сервера от Али - Ключ не найден: %s", e)
            return response
        self.get_products_to_send(products)
        logger.debug('fill_get_products_to_send (AliApiAsync) finished')

    async def search_by_sku_async(self) -> Dict:
        logger.debug('search_by_sku_async (AliApiAsync) started')

        response = await AliApiAsync.send_post(AliApi.SEARCH_URL, self.search_headers, json.dumps(self.search_data))
        logger.debug('search_by_sku_async (AliApiAsync) finished')
        return response

    async def send_remains_async(self) -> dict:
        """
        Отправляет оставшиеся товары на сервер Али.

        :return: Словарь с ошибками, если они есть, в противном случае пустой словарь.
        """
        ...
        logger.debug('send_remains_async (AliApiAsync) started')
        data = {"products": self.products_to_send}
        response = await AliApiAsync.send_post(AliApi.SEND_REMAINS_URL, self.send_remains_headers, json.dumps(data))
        exception = response.get('error')
        if exception:
            return {'error': f'Ошибка отправки товаров на Али. Сервер вернул исключение - {exception}'}
        results: list = response.get('results')
        if results:
            errors = {result.get('external_id'): result.get('errors') for result in results if result.get('errors')}
            logger.debug(f'response errors messages {errors=}')
        else:
            errors = {'error': f'Ошибка отправки товаров на Али. Сервер вернул не понятно что - {response}'}
        logger.debug('send_remains_async (AliApiAsync) FINISHED')
        return errors

    @staticmethod
    async def send_post(url: str, headers: dict, data: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(url,
                                    headers=headers,
                                    data=data) as response:
                logger.info(f'HTTP Request: POST {url}, {response.status}')
                try:
                    response.raise_for_status()
                except (aiohttp.ClientResponseError,
                        aiohttp.ClientConnectionError,
                        asyncio.TimeoutError) as e:
                    logger.error(f'REQUEST ERROR {e}')
                    return {'error': str(e)}

                response_text = await response.text()
                logger.debug('send_remains_async to ali finished')
                return json.loads(response_text)
