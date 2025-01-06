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

    def __init__(self,
                 url: Optional[str] = None,
                 headers: Optional[Dict[str, str]] = None,
                 json_dict: Optional[Dict[str, str]] = None,
                 files: Optional[aiohttp.FormData] = None,
                 query_params: Optional[Dict[str, str]] = None):
        self.url = url
        self.headers = headers
        self.json = json_dict
        self.files = files
        self.query_params = query_params

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
                              ) -> Dict:
        url = url or self.url
        headers = headers or self.headers
        json_data = json_data or self.json
        files = files or self.files
        params = params or self.query_params

        logger.debug(f'\n{url=}\n'
                     f'{headers=}\n'
                     f'{json_data=}\n'
                     f'{files=}\n'
                     f'{params=}\n')

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url,
                                    headers=headers,
                                    json=json_data,
                                    data=files,
                                    params=params) as response:
                logger.info(f'HTTP async Request: POST {url}, {response.status}')
                response_json = await response.json()

                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError:
                    logger.error(f'REQUEST ERROR {response_json.get("message")}')
                    return {'error': response_json.get("message")}

                return response_json

    async def send_get_async(self, url=None, headers=None, params=None) -> dict:
        url = url or self.url
        headers = headers or self.headers
        logger.debug(f'Sending GET request: {url=}, {headers=}, {params=}')
        params = params or self.query_params
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers, params=params) as response:
                logger.info(f'HTTP async Request: GET {url}, {response.status}')
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f'REQUEST ERROR {e}')
                    return {'error': str(e)}
                if 'image' in response.headers.get('Content-Type', ''):
                    image_data = await response.read()
                    return {'image_data': image_data}
                return await response.json()
