from Request import Request
from logger import logger
import time


class BifitSession(Request):

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.token = None
        self.expiration_time = None
        self.refresh_token = None
        logger.debug('создал класс сессии бифит-касса')

    async def get_token_async(self):
        logger.debug('get_token_async started')
        auth_url = 'https://kassa.bifit.com/cashdesk-api/v1/oauth/token'
        if self.token is None:
            logger.debug('старого токена нет, пробую получить')
            body = {"username": self.username,
                    "password": self.password,
                    "client_id": "cashdesk-rest-client",
                    "client_secret": "cashdesk-rest-client",
                    "grant_type": "password"}
            response = await self.send_post_async(url=auth_url, data=body)
            self.token = response.get('token')
            self.refresh_token = response.get('refresh_token')
            expires_in = response.get('expires_in')
            try:
                if expires_in is None:
                    raise ValueError("expires_in is None")
                expires_in = float(expires_in)
            except (TypeError, ValueError) as e:
                logger.error(f'Ошибка рассчета времени истечения токена - {e}')
            else:
                self.expiration_time = time.time() + expires_in
            ...
