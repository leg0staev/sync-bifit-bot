import json
import time
from typing import Any

import requests

from Clases.ApiMarketplaces.Ozon.SendStocksResponce import SendStocksResponse
from Clases.ApiMarketplaces.Ozon.Warehouse import Warehouse


class OzonApi:
    GET_ALL_PRODUCTS_URL_V2 = 'https://api-seller.ozon.ru/v2/product/list'
    GET_ALL_PRODUCTS_URL_V3 = 'https://api-seller.ozon.ru/v3/product/list'
    GET_ALL_WAREHOUSES_URL = 'https://api-seller.ozon.ru/v1/warehouse/list'
    SEND_REMAINS_URL = 'https://api-seller.ozon.ru/v2/products/stocks'
    GET_ALL_POSTINGS_URL = 'https://api-seller.ozon.ru/v3/posting/fbs/unfulfilled/list'

    def __init__(self, token: str, id_: str) -> None:

        self.token = token
        self.id = id_

        self.headers = {
            'Content-Type': 'application/json',
            'Client-Id': self.id,
            'Api-Key': self.token,
        }

        self.errors = {}

    def get_all_products(self):

        response = requests.post(url=OzonApi.GET_ALL_PRODUCTS_URL_V2, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f'Error: {e}'
        return response.json()

    def send_remains(self, ozon_prod_dict: dict[str, str], bifit_remains: dict[str, int],
                     warehouses: list[Warehouse]) -> dict[str, Any]:

        stocks = self.get_remains_list(ozon_prod_dict, bifit_remains, warehouses)

        for stock_chunk in self.chunk_stocks(stocks, 100):
            data = {"stocks": stock_chunk}
            try:
                response = requests.post(url=OzonApi.SEND_REMAINS_URL, headers=self.headers, data=json.dumps(data))
                response.raise_for_status()
                stock_response = SendStocksResponse.from_dict(response.json())
                for result in stock_response.results:
                    if result.has_errors():
                        self.errors[result.offer_id] = result.errors
            except requests.RequestException as e:
                self.errors['RequestException'] = e

            time.sleep(1)

        return self.errors

    def get_warehouses(self):

        response = requests.post(url=OzonApi.GET_ALL_WAREHOUSES_URL, headers=self.headers)

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f'Error: {e}'

        return response.json()

    @staticmethod
    def distribute_remains(remains_: int, wh_quantity: int) -> list[int]:
        for_each_warehouse = remains_ // wh_quantity  # Количество товара для каждого склада
        indivisible_remains = remains_ % wh_quantity  # Неделимый остаток
        distribution = [for_each_warehouse] * wh_quantity
        distribution[0] += indivisible_remains  # Первому складу достается неделимый остаток
        return distribution

    @staticmethod
    def chunk_stocks(stock_list: list[dict], chunk_size: int) -> list[dict]:
        for i in range(0, len(stock_list), chunk_size):
            yield stock_list[i:i + chunk_size]

    @staticmethod
    def get_remains_list(prod_dict: dict[str, str],
                         bifit_remains: dict[str, int],
                         warehouses: list[Warehouse]) -> list:
        result_list = []
        for product_sku, product_id in prod_dict.items():
            if product_sku in bifit_remains:
                remains = bifit_remains[product_sku]
                remains_distribution = OzonApi.distribute_remains(remains,
                                                                  len(warehouses))
                for w, remains_to_upload in zip(warehouses, remains_distribution):
                    item = {
                        "offer_id": product_sku,
                        "product_id": product_id,
                        "stock": remains_to_upload,
                        "warehouse_id": w.id,
                    }
                    result_list.append(item)
        return result_list

    @staticmethod
    def check_sand_remains_response(response: dict) -> None | dict[str, str]:
        sand_results = response.get('result')
        if sand_results is not None:
            errors = {}
            for result in sand_results:
                error = result.get('errors')
                offer_id = result.get('offer_id')
                if error == []:
                    continue
                if error is None or offer_id is None:
                    return {'error': f'неожиданный формат данных - {result}'}
                errors[offer_id] = error
            return errors
        return {'error': f'неожиданный формат данных - {response}'}