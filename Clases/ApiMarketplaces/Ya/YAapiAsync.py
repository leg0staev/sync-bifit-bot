import json

import aiohttp

from Clases.ApiMarketplaces.Ya.YAapi import YAapi
from Clases.BifitApi.Good import Good
from logger import logger


class YAapiAsync(YAapi):

    def __init__(self,
                 token: str,
                 campaign_id: int,
                 warehouse_id: int,
                 goods_dict: dict[str, int] = None,
                 goods_set: set[Good] = None) -> None:
        super(YAapiAsync, self).__init__(token, campaign_id, warehouse_id, goods_dict, goods_set)

    async def send_remains_async(self) -> dict:
        """
        Асинхронная версия метода send_remains.

        :return: Словарь с ответом сервера
        """
        logger.debug('send_remains_async (YAapiAsync) started')
        url = f'{YAapi.BASE_URL}/campaigns/{self.campaign_id}/offers/stocks'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        data = {"skus": self.remains}

        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, data=json.dumps(data)) as response:
                logger.info(f'HTTP Request: PUT {url}, {response.status}')
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'ошибка отправки остатков в Яндекс - {e}')
                    return {'error': str(e)}

                response_text = await response.text()
                logger.debug('send_remains_async (YAapiAsync) finished')
                return json.loads(response_text)

    async def send_remains_async_v2(self) -> dict:
        """
        Асинхронная версия метода send_remains.

        :return: Словарь с ответом сервера
        """
        logger.debug('send_remains_async (YAapiAsync) started')
        url = f'{YAapi.BASE_URL}/campaigns/{self.campaign_id}/offers/stocks'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        data = {"skus": self.remains}

        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, data=json.dumps(data)) as response:
                logger.info(f'HTTP Request: PUT {url}, {response.status}')
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'ошибка отправки остатков в Яндекс - {e}')
                    return {'error': str(e)}

                response_text = await response.text()
                logger.debug('send_remains_async (YAapiAsync) finished')
                return json.loads(response_text)