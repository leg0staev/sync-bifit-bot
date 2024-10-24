from Clases.BifitApi.Request import *


class SendCSVStocksRequest(Request):
    """Класс запроса на отправку остатков через CSV"""

    def __init__(self, token: str, org_id: str, csv_str: str) -> None:
        super().__init__()

        self.url = f'{Request.BIFIT_API_URL}/protected/goods/csv/upload'

        self.headers = {
            'Authorization': f'Bearer {token}',
            'accept': '*/*',
        }
        self.query_params = {
            'organization_id': org_id,
            'charset': 'utf-8',
        }

        self.files = aiohttp.FormData()
        self.files.add_field('file', csv_str, filename='nomenclatures.csv', content_type='text/csv')

