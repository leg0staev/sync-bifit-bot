from Clases.BifitApi.Request import Request


class OrgListReq(Request):
    """Класс запроса списка организаций"""
    def __init__(self, url: str, token: str) -> None:

        super().__init__()

        self.url = url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

