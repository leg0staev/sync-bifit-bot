from Clases.BifitApi.Request import Request


class ContactorsRequest(Request):
    """Класс запроса списка поставщиков"""
    def __init__(self, url: str, token: str, org_id: str, contactors_ids: list[int]) -> None:
        super().__init__()

        self.url = url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        self.query_params = {
            'organization_id': org_id,
        }

        self.json = contactors_ids
