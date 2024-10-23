from Clases.BifitApi.Request import Request


class ParentNomenclaturesReq(Request):
    def __init__(self, token, nomenclature_id) -> None:
        super().__init__()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        self.url = f'http://kassa.bifit.com/cashdesk-api/v1/protected/nomenclatures/{nomenclature_id}/parents'
        self.query_params = {
            'includeNomenclature': 'false',
        }