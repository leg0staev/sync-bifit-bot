from logger import logger

from Clases.BifitApi.Request import Request


class ParentNomenclaturesReq(Request):
    """Класс запроса списка родительских номенклатур"""

    def __init__(self, url: str, token: str, nomenclature_id: int) -> None:
        super().__init__()
        self.headers = {
            'Authorization': f'Bearer {token}'
        }

        self.url = f'{url}/{nomenclature_id}/parents'
        self.query_params = {
            'includeNomenclature': 'false',
        }
