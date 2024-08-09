from Clases.BifitApi.Request import *


class TradeObjListReq(Request):
    def __init__(self,
                 token,
                 org_id):
        super().__init__()

        self.url = f'https://kassa.bifit.com/cashdesk-api/v1/protected/trade_objects/list/read_all'

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        self.query_params = {
            'organization_id': org_id,
            'return_all': 'True',
        }

        # self.body = {"organization_id": f"{org_id}",
        #              "return_all": "true"}
