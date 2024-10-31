from Clases.BifitApi.Request import Request


class GoodsListReq(Request):
    """Класс запроса списка всех товаров"""
    def __init__(self,
                 url: str,
                 token: str,
                 org_id: str,
                 trade_obj_id: str,
                 with_zero: str = 'True',
                 goods_type: str = 'POSITIVE,NEGATIVE,NULL') -> None:
        super().__init__()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        self.url = url
        self.query_params = {
            'organization_id': org_id,
            'with_zero': with_zero,
            'goods_type': goods_type,
        }

        self.body = [f'{trade_obj_id}']
