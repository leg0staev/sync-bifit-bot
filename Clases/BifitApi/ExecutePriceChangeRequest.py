from Clases.BifitApi.Request import Request


class ExecutePriceChangeRequest(Request):

    def __init__(self,
                 url: str,
                 token: str,
                 org_id: str,
                 doc_ids: list[int]) -> None:
        super().__init__()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'Accept': '*/*'
        }
        self.url = f'{url}/protected/price_change/{org_id}/list/execute'

        self.json = doc_ids
