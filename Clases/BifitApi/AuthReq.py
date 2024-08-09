from Clases.BifitApi.Request import Request


class AuthReq(Request):
    def __init__(self, username, password):
        super().__init__()
        self.url = 'https://kassa.bifit.com/cashdesk-api/v1/oauth/token'

        self.body = {"username": username,
                     "password": password,
                     "client_id": "cashdesk-rest-client",
                     "client_secret": "cashdesk-rest-client",
                     "grant_type": "password"}

    def __str__(self):
        return (f'self.query_str - {self.url}\n'
                f'self.body - {self.body}\n')
