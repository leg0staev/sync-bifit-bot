import json
from typing import Dict

import requests

from Clases.ApiMarketplaces.Ali.AliProduct import AliProduct
from Clases.ApiMarketplaces.Ali.SendStocksResponse import SendStocksResponse
from Clases.BifitApi.Good import Good
from logger import logger


class AliApi:
    BASE_URL = 'https://openapi.aliexpress.ru/api/v1'
    SEARCH_URL = f'{BASE_URL}/scroll-short-product-by-filter'
    SEND_REMAINS_URL = f'{BASE_URL}/product/update-sku-stock'

    def __init__(self,
                 token: str,
                 products_dict: dict[str, int] = None,
                 product_set: set[Good] = None) -> None:
        """
            Инициализация класса AliApi.

            :param token: токен для доступа к API
            :param products_dict: словарь с SKU товаров и их количеством
            :param product_set: множество с товарами али
            """
        self.token = token
        self.errors = {}
        self.bifit_products_dict: dict[str, int] | None = products_dict
        self.bifit_products_set: set[Good] | None = product_set

        content_values = list(self.bifit_products_dict.keys()) or \
                         [good.nomenclature.barcode for good in product_set]

        self.search_headers = {
            'x-auth-token': self.token,
            'Content-Type': 'application/json',
            'x-request-locale': 'ru_RU'
        }

        self.send_remains_headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'x-auth-token': self.token
        }

        self.search_data = {
            "filter": {
                "search_content": {
                    "content_values": content_values,
                    "content_type": "SKU_SELLER_SKU"
                }
            },
            "limit": 50
        }

        self.products_to_send = []
        # self.fill_get_products_to_send()

    def fill_get_products_to_send(self):
        logger.debug('fill_get_products_to_send (AliApi) started')
        return self.get_products_to_send([AliProduct(p) for p in self.search_by_sku()['data']])

    def get_products_to_send(self, products_list: list[AliProduct]) -> None:
        logger.debug('get_products_to_send (AliApi) started')
        for product in products_list:
            skus_list = []
            for sku in product.skus:
                if sku.code in self.bifit_products_dict:
                    sku_info = {
                        "sku_code": sku.code,
                        "inventory": self.bifit_products_dict[sku.code]
                    }
                    skus_list.append(sku_info)

            good = {
                "product_id": product.id,
                "skus": skus_list
            }
            self.products_to_send.append(good)

    def search_by_sku(self) -> dict:
        logger.debug('search_by_sku (AliApi) started')
        response = requests.post(url=AliApi.SEARCH_URL,
                                 headers=self.search_headers,
                                 data=json.dumps(self.search_data))

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
        logger.debug('search_by_sku (AliApi) finished')
        return response.json()

    def send_remains(self) -> Dict[str, str]:
        logger.debug('send_remains (AliApi) started')
        data = {"products": self.products_to_send}

        try:
            response = requests.post(url=AliApi.SEARCH_URL,
                                     headers=self.send_remains_headers,
                                     data=json.dumps(data))
            logger.info(f'HTTP Request: POST {AliApi.SEARCH_URL}, {response.status_code}')
            response.raise_for_status()
            stock_response = SendStocksResponse.from_dict(response.json())
            for result in stock_response.results:
                if result.has_errors():
                    self.errors[result.external_id] = result.errors
        except requests.exceptions.RequestException as e:
            self.errors['request_exception'] = str(e)
        logger.debug('send_remains (AliApi) finished')
        return self.errors
