from Clases.BifitApi.Request import Request


class GoodsRemainsReq(Request):
    def __init__(self,
                 token,
                 org_id,
                 trade_obj_id):
        super().__init__()

        self.url = f'{Request.BIFIT_API_URL}/protected/goods/quantity'

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        self.body = {"organization_id": f"{org_id}",
                     "trade_object_id": f"{trade_obj_id}"}
