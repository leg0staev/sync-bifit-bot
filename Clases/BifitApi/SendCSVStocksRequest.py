from Clases.BifitApi.Request import *


class SendCSVStocksRequest(Request):
    """Класс запроса на отправку остатков через CSV"""

    def __init__(self, token: str, org_id: str, csv_str: str) -> None:
        super().__init__()

        self.url = 'https://kassa.bifit.com/cashdesk-api/v1/protected/goods/csv/upload'

        self.headers = {
            'Authorization': f'Bearer {token}',
            'accept': '*/*',
        }
        self.query_params = {
            'organization_id': org_id,
            'charset': 'utf-8',
        }
        self.files = {
            'file': ('nomenclatures.csv', csv_str, 'text/csv')  # имя файла, данные, тип
        }
