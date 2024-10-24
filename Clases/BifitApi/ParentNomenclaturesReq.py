from logger import logger

from Clases.BifitApi.Request import Request


class ParentNomenclaturesReq(Request):
    def __init__(self, token, nomenclature_id) -> None:
        super().__init__()
        self.headers = {
            'Authorization': f'Bearer {token}'
        }

        logger.debug(f'{self.headers=}')
        self.url = f'{Request.BIFIT_API_URL}/protected/nomenclatures/{nomenclature_id}/parents'
        self.query_params = {
            'includeNomenclature': 'false',
        }
