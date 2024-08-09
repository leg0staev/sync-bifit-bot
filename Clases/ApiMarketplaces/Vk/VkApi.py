import requests
import json
import time


class VkApi:
    BASE_URL = 'https://api.vk.com/method'
    ALL_PRODUCTS_URL = f'{BASE_URL}/market.get'
    EDIT_PRODUCT_URL = f'{BASE_URL}/market.edit'

    def __init__(self, token: str, owner_id: int, api_version: float) -> None:
        self.token = token
        self.owner_id = owner_id
        self.api_version = api_version
        self.headers = {
            'Authorization': f'Bearer {self.token}',
        }

    def get_all_products(self):

        params = {
            'owner_id': self.owner_id,
            'v': self.api_version,
        }

        response = requests.post(url=VkApi.ALL_PRODUCTS_URL, headers=self.headers, params=params)
        if response.status_code != 200:
            return f'Error: status code - {response.status_code}, {response.content.decode("utf8")}'
        return json.loads(response.content.decode("utf8"))

    def send_remains(self, vk_prod_dict: dict[str:str], bifit_remains: dict[str:int]) -> tuple:

        responses = []
        request_exceptions = {}

        for product_sku, vk_item_id in vk_prod_dict.items():
            if product_sku in bifit_remains:
                params = {
                    'owner_id': self.owner_id,
                    'v': self.api_version,
                    'item_id': vk_item_id,
                    'stock_amount': bifit_remains[product_sku]
                }

                response = requests.post(url=VkApi.EDIT_PRODUCT_URL, headers=self.headers, params=params)

                try:
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    request_exceptions[product_sku] = {'request_exception': str(e)}

                content = response.json()

                responses.append(content)

            time.sleep(0.3)

        return request_exceptions, responses
