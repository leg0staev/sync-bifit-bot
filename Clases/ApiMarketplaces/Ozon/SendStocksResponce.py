from Clases.ApiMarketplaces.Ozon.SendStocksResult import SendStocksResult
from typing import Any


class SendStocksResponse:
    def __init__(self, results: list[SendStocksResult]) -> None:
        self.results = results

    @staticmethod
    def from_dict(data: dict[str:Any]) -> 'SendStocksResponse':
        results = [SendStocksResult(warehouse_id=item['warehouse_id'],
                                    product_id=item['product_id'],
                                    offer_id=item['offer_id'],
                                    updated=item['updated'],
                                    errors=item['errors']) for item in data['result']]
        return SendStocksResponse(results=results)
