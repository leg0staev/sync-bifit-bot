import json
from typing import Dict, Optional

import aiohttp
import requests

from logger import logger


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
        self.body: Optional[Dict[str, str]] = None
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
        data = json.dumps(self.body)
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

    async def send_post_async(self) -> Dict[str, str]:

        url = self.url
        headers = self.headers
        data = self.body
        params = self.query_params

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url,
                                    headers=headers,
                                    json=data,
                                    params=params) as response:
                logger.info(f'HTTP async Request: POST {url}, {response.status}')

                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'REQUEST ERROR {e}')
                    return {'error': str(e)}

                response_text = await response.text()
                return json.loads(response_text)

            # Пример использования асинхронного метода
            # async def main():
            #     request = Request()
            #     request.query_str = "http://example.com"
            #     request.headers = {"Content-Type": "application/json"}
            #     request.body = json.dumps({"key": "value"})
            #     result = await request.send_post_async()
            #     print(result)

            # asyncio.run(main())
