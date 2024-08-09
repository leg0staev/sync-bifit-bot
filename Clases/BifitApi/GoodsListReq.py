from Clases.BifitApi.Request import Request


class GoodsListReq(Request):
    def __init__(self,
                 token,
                 org_id,
                 trade_obj_id,
                 with_zero='True',
                 goods_type='POSITIVE,NEGATIVE,NULL'):
        super().__init__()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        self.url = f'https://kassa.bifit.com/cashdesk-api/v1/protected/goods/list/read'
        self.query_params = {
            'organization_id': org_id,
            'with_zero': with_zero,
            'goods_type': goods_type,
        }

        self.body = [f'{trade_obj_id}']
