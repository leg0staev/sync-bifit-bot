import asyncio
import json

import aiohttp

from Clases.ApiMarketplaces.Vk.VkApi import VkApi
from Clases.BifitApi.Good import Good
from logger import logger
from methods.sync_methods import get_selling_price


class VkApiAsync(VkApi):

    DELAY = 0.35
    MAX_CONCURRENCY = 3

    def __init__(self, token: str, owner_id: int, api_version: float) -> None:
        super(VkApiAsync, self).__init__(token, owner_id, api_version)

    async def get_all_products_async(self):
        """Запрашивает все товары из VK асинхронно."""
        logger.debug('get_all_products_async (VkApiAsync) началась')

        offset = 0
        count_per_request = 100
        vk_products_items = []

        async with aiohttp.ClientSession() as session:

            while True:

                params = {
                    'owner_id': self.owner_id,
                    'v': self.api_version,
                    'count': count_per_request,
                    'offset': offset,
                }

                async with session.post(VkApi.ALL_PRODUCTS_URL, headers=self.headers, params=params) as response:
                    logger.info(f"HTTP Request: POST {VkApi.ALL_PRODUCTS_URL}, {response.status}")
                    try:
                        response.raise_for_status()
                    except aiohttp.ClientResponseError as e:
                        logger.error(f"ошибка получения товаров в ВК: {str(e)}")
                        return ['error', f'ошибка получения товаров в ВК - {str(e)}']

                    response_text = await response.text()
                    response = json.loads(response_text).get('response', {})

                    vk_products_items.extend(response.get('items', []))
                    total_count = response.get('count', 0)

                    logger.debug('получил количество товаров в ответе ВК - %s', total_count)
                    logger.info('Загружено %d из %d', len(vk_products_items), total_count)

                    if offset + count_per_request >= total_count:
                        break

                    offset += count_per_request
                    await asyncio.sleep(VkApiAsync.DELAY)

        logger.debug('get_all_products_async (VkApiAsync) завершилась без ошибок')
        return vk_products_items


    async def send_remains_async(self,
                                 vk_prod_dict: dict[str, str],
                                 bifit_remains: dict[str, int]) -> dict[str, dict[str, str]]:
        """Send remaining stock to VK asynchronously."""
        logger.debug('send_remains_async (VkApiAsync) started')

        errors = {}

        for product_sku, vk_item_id in vk_prod_dict.items():
            if product_sku in bifit_remains:
                params = {
                    'owner_id': self.owner_id,
                    'v': self.api_version,
                    'item_id': vk_item_id,
                    'stock_amount': bifit_remains[product_sku]
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(VkApi.EDIT_PRODUCT_URL, headers=self.headers, params=params) as response:
                        logger.info(
                            f"HTTP Request: POST {VkApi.EDIT_PRODUCT_URL}, {response.status}, PRODUCT {product_sku}")
                        try:
                            response.raise_for_status()
                        except aiohttp.ClientResponseError as e:
                            logger.error(f"VkApiAsync Request error: {str(e)}")
                            errors[product_sku] = {'Ошибка обновления товара': str(e)}

                        content = await response.text()
                        response_json = json.loads(content)
                        logger.debug(f'Server response: {response_json}')
                        error = VkApiAsync.check_errors(response_json)
                        if error:
                            errors[product_sku] = error
                            logger.error(f'PRODUCT {product_sku} - {error}')
            await asyncio.sleep(VkApiAsync.DELAY)

        logger.debug('send_remains_async (VkApiAsync) finished')
        return errors

    async def send_remains_async_v2(self,
                                    vk_prod_dict: dict[str, str],
                                    bifit_remains: set[Good]) -> dict[str, dict]:
        """Send remaining stock to VK asynchronously."""
        logger.debug('send_remains_async_v2 (VkApiAsync) запущена')

        errors: dict[str, dict] = {}

        async with aiohttp.ClientSession() as session:

            for good in bifit_remains:
                if good.nomenclature.barcode not in vk_prod_dict:
                    logger.warning('Товар с штрихкодом - %s отсутствует в словаре ВК. пропускаю его', good.nomenclature.barcode)
                    continue


                params = {
                    'owner_id': self.owner_id,
                    'v': self.api_version,
                    'item_id': vk_prod_dict[good.nomenclature.barcode],
                    'stock_amount': good.goods.quantity,
                    'price': get_selling_price(good)
                }

                logger.debug('штрихкод товара: %s\nparams: %s', good.nomenclature.barcode, params)

                async with session.post(self.EDIT_PRODUCT_URL, headers=self.headers, params=params) as response:
                    logger.info(f"HTTP POST {self.EDIT_PRODUCT_URL} {response.status}, "
                                f"PRODUCT {good.nomenclature.barcode}")
                    try:
                        response.raise_for_status()
                    except aiohttp.ClientResponseError as e:
                        logger.error(f"VkApiAsync Request error: {str(e)}")
                        errors[good.nomenclature.barcode] = {'Сервер вернул ошибку': str(e)}

                    else:
                        text = await response.text()
                        response_json = json.loads(text)

                        logger.debug(f'Ответ сервера: {response_json}')
                        error = self.check_errors(response_json)
                        if error:
                            logger.error(f'{good.nomenclature.barcode}: {error}')
                            errors[good.nomenclature.barcode] = {'Ошибка обновления товара': str(error)}

                await asyncio.sleep(VkApiAsync.DELAY)

        logger.debug('send_remains_async_v2 (VkApiAsync) завершена')
        return errors

    @staticmethod
    def check_errors(response_data: dict) -> tuple[str, str] | None:
        """Check for errors in VK API response."""
        if 'error' in response_data:
            error_code = response_data.get('error').get('error_code', 'error code parsing failed')
            error_message = response_data.get('error').get('error_msg', 'error msg parsing failed')
            return error_code, error_message
        return None
