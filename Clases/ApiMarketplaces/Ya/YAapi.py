import requests
import json
from datetime import datetime, timezone


class YAapi:
    BASE_URL = 'https://api.partner.market.yandex.ru'

    def __init__(self, token: str, campaign_id: int, warehouse_id: int, goods_dict: dict[str, int] = None) -> None:
        """
        Инициализация класса YAapi.

        :param token: токен для доступа к API
        :param campaign_id: идентификатор кампании
        :param warehouse_id: идентификатор склада
        :param goods_dict: словарь с SKU товаров и их количеством
        """
        self.token = token
        self.campaign_id = campaign_id
        self.warehouse_id = warehouse_id
        self.remains = []
        if goods_dict:
            self.get_remains(goods_dict)

    def get_remains(self, skus: dict[str, int]) -> None:
        """
        Получает остаток товаров на складе.

        :param skus: словарь с SKU товаров и их количеством
        """
        for sku, count in skus.items():
            good = {
                "sku": sku,
                "warehouseId": self.warehouse_id,
                "items": [
                    {
                        "count": count,
                        "type": "FIT",
                        "updatedAt": self._get_utc_datetime_string()
                    }
                ]
            }
            self.remains.append(good)

    def send_remains(self) -> dict:
        """
        Отправляет данные об остатках товаров на складе в Яндекс.Маркет.

        :return: статус-код ответа и словарь с ответом сервера
        """
        url = f'{YAapi.BASE_URL}/campaigns/{self.campaign_id}/offers/stocks'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        data = {"skus": self.remains}

        try:
            response = requests.put(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {'errors': str(e)}

        return response.json()

    @staticmethod
    def _get_utc_datetime_string() -> str:
        """
        Возвращает текущую дату и время в формате UTC.

        :return: строка с датой и временем в формате UTC
        """
        return datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
