from Clases.BifitApi.Request import Request


class GetNomenclaturesRequest(Request):
    """Класс запроса списка номенклатур по списку штрихкодов"""
    def __init__(self,
                 url: str,
                 token: str,
                 org_id: str,
                 barcodes: list[str]) -> None:

        super().__init__()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        self.url = url
        self.query_params = {
            'organization_id': org_id
        }

        self.json = barcodes
