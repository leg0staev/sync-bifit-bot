from Clases.ApiMarketplaces.Vk.VKProduct import VkProduct


class VkProdResponse:
    def __init__(self, data) -> None:
        self.count = data['response']['count']
        self.products = [VkProduct(p) for p in data['response']['items']]

    def get_all_skus(self) -> list[str]:
        return [product.sku for product in self.products]

    def get_skus_id_dict(self) -> dict[str:str]:
        return {product.sku: product.id for product in self.products}
