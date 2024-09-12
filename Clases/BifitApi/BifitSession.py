import time

from Clases.BifitApi.Request import Request
from logger import logger


class BifitSession(Request):
    AUTH_URL = 'https://kassa.bifit.com/cashdesk-api/v1/oauth/token'

    __slots__ = 'username', 'password', 'access_token', 'expiration_time', 'refresh_token'

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.access_token = None
        self.expiration_time = None
        self.refresh_token = None
        logger.debug('создал класс сессии бифит-касса')

    async def initialize(self) -> None:
        """Асинхронная инициализация токена."""
        await self.get_new_token_async()

    @property
    async def token(self) -> str:
        """Получение токена из состояния класса"""
        logger.debug('get_token started')
        if self.expiration_time is None:
            logger.debug('старого токена нет, пробую получить')
            await self.get_new_token_async()
        elif self.expiration_time < time.time():
            logger.debug('старый токен истек, пробую получить новый')
            await self.get_token_by_refresh_async()
        else:
            logger.debug('токен существует и он еще не истек')
        return self.access_token

    async def get_token_by_refresh_async(self):
        """Получение токена, если он истек."""
        logger.debug('get_token_by_refresh_async started')
        body = {
            "refresh_token": self.refresh_token,
            "client_id": "cashdesk-rest-client",
            "client_secret": "cashdesk-rest-client",
            "grant_type": "refresh_token",
        }
        response = await self.send_post_async(url=BifitSession.AUTH_URL, data=body)
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
        response = await self.send_post_async(url=BifitSession.AUTH_URL, data=body)
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
