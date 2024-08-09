from Clases.ApiMarketplaces.Ali.SendStocksResult import SendStocksResult
from typing import Any


class SendStocksResponse:
    def __init__(self, group_id: str, results: list[SendStocksResult]) -> None:
        self.group_id = group_id
        self.results = results

    @staticmethod
    def from_dict(data: dict[str:Any]) -> 'SendStocksResponse':
        results = [SendStocksResult(ok=item['ok'],
                                    task_id=item['task_id'],
                                    errors=item.get('errors', []),
                                    external_id=item['external_id']) for item in data['results']]
        return SendStocksResponse(group_id=data['group_id'], results=results)

    def has_errors(self) -> bool:
        return any(result.has_errors() for result in self.results)

    def __repr__(self):
        return f"Response(group_id={self.group_id}, results={self.results})"
