from Clases.BifitApi.Request import *


class OrgListReq(Request):
    def __init__(self, token):

        super().__init__()

        self.url = f'{Request.BIFIT_API_URL}/protected/organizations/list/read_all'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

