from Clases.BifitApi.Request import *


class TradeObjListReq(Request):
    """Класс запроса списка торговых объектов"""
    def __init__(self, url: str, token: str, org_id: str) -> None:
        super().__init__()

        self.url = url

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        self.query_params = {
            'organization_id': org_id,
            'return_all': 'True',
        }
