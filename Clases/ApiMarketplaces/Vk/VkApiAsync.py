import asyncio
import json

import aiohttp

from Clases.ApiMarketplaces.Vk.VkApi import VkApi
from logger import logger


class VkApiAsync(VkApi):
    def __init__(self, token: str, owner_id: int, api_version: float) -> None:
        super(VkApiAsync, self).__init__(token, owner_id, api_version)

    async def get_all_products_async(self) -> dict:
        """Fetch all products from VK asynchronously."""
        logger.debug('get_all_products_async (VkApiAsync) started')

        params = {
            'owner_id': self.owner_id,
            'v': self.api_version,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(VkApi.ALL_PRODUCTS_URL, headers=self.headers, params=params) as response:
                logger.info(f"HTTP Request: POST {VkApi.ALL_PRODUCTS_URL}, {response.status}")
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f"ошибка получения товаров в ВК: {str(e)}")
                    return {'error': f'ошибка получения товаров в ВК - {str(e)}'}
                response_text = await response.text()
                # logger.debug(f'{response_text=}')
                logger.debug('get_all_products_async (VkApiAsync) finished')
                return json.loads(response_text)

    async def send_remains_async(self, vk_prod_dict: dict[str, str], bifit_remains: dict[str, int]) -> dict[str, dict[str, str]]:
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
            await asyncio.sleep(0.3)

        logger.debug('send_remains_async (VkApiAsync) finished')
        return errors

    @staticmethod
    def check_errors(response_data: dict) -> tuple[str, str] | None:
        """Check for errors in VK API response."""
        if 'error' in response_data:
            error_code = response_data.get('error').get('error_code', 'error code parsing failed')
            error_message = response_data.get('error').get('error_msg', 'error msg parsing failed')
            return error_code, error_message
        return None
