from Clases.ApiMarketplaces.Ozon.OzonProduct import OzonProduct


class OzonProdResponse:
    def __init__(self, data: dict) -> None:
        self.items = [OzonProduct(i) for i in data['result']['items']]
        self.total = data['result']['total']
        self.last_id = data['result']['last_id']

    def get_skus_id_dict(self) -> dict[str:str]:
        """возвращает словарь штрихкод:id на озон"""
        return {product.offer_id: product.product_id for product in self.items}

# {
#     "result": {
#         "items": [
#             {
#                 "product_id": 651604248,
#                 "offer_id": "4660199150175",
#                 "is_fbo_visible": false,
#                 "is_fbs_visible": false,
#                 "archived": false,
#                 "is_discounted": false
#             }
#         ],
#         "total": 1,
#         "last_id": "WyI2NTE2MDQyNDgiLCI2NTE2MDQyNDgiXQ=="
#     }
# }
