import json
from typing import Dict, Optional

import aiohttp
import requests

from logger import logger
from Exceptions.ResponseContentException import ResponseContentException
from Exceptions.ResponseStatusException import ResponseStatusException


class Request:
    """
    Класс для отправки HTTP-запросов.

    Атрибуты:
        url (str): URL запроса.
        headers (dict): Заголовки запроса.
        body (dict): Тело запроса в формате JSON.
        query_params (dict): Параметры запроса.
    """

    def __init__(self):
        self.url: Optional[str] = None
        self.headers: Optional[Dict[str, str]] = None
        self.json: Optional[Dict[str, str]] = None
        self.files: Optional[aiohttp.FormData] = None
        self.query_params: Optional[Dict[str, str]] = None

    def send_post(self) -> Dict[str, str]:

        """
        Отправляет POST-запрос и возвращает ответ в формате JSON.

        Возвращает:
            dict: JSON-ответ от сервера или сообщение об ошибке.

        Поднимает:
            requests.exceptions.RequestException: ошибка запроса.
        """

        url = self.url
        headers = self.headers
        data = json.dumps(self.json)
        params = self.query_params

        response = requests.post(url=url,
                                 headers=headers,
                                 data=data,
                                 params=params)

        logger.info(f'HTTP sync Request: POST {url}, {response.status_code}')

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f'REQUEST ERROR {e}')
            return {'error': str(e)}

        return response.json()

    async def send_post_async(self,
                              url=None,
                              headers=None,
                              json_data=None,
                              files=None,
                              params=None,
                              ) -> Dict[str, str]:
        url = url or self.url
        headers = headers or self.headers
        json_data = json_data or self.json
        files = files or self.files
        params = params or self.query_params

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url,
                                    headers=headers,
                                    json=json_data,
                                    data=files,
                                    params=params) as response:
                logger.info(f'HTTP async Request: POST {url}, {response.status}')

                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'REQUEST ERROR {e}')
                    return {'error': str(e)}

                response_json = await response.json()
                return response_json

            # Пример использования асинхронного метода
            # async def main():
            #     request = Request()
            #     request.query_str = "http://example.com"
            #     request.headers = {"Content-Type": "application/json"}
            #     request.body = json.dumps({"key": "value"})
            #     result = await request.send_post_async()
            #     print(result)

            # asyncio.run(main())
