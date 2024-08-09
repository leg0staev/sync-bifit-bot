from Clases.BifitApi.Request import *


class OrgListReq(Request):
    def __init__(self, token):

        super().__init__()

        self.url = 'https://kassa.bifit.com/cashdesk-api/v1/protected/organizations/list/read_all'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

