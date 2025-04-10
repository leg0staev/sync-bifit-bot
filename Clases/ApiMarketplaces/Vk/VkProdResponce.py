from Clases.ApiMarketplaces.Vk.VKProduct import VkProduct
from logger import logger


class VkProdResponse:
    def __init__(self, data) -> None:
        response = data.get('response')
        self.count = response.get('count')
        # self.products = [VkProduct(p) for p in response.get('items')]
        self.products = []
        items = response.get('items')
        for item in response.get('items'):
            vk_prod = VkProduct(item)
            logger.debug('сформировал товар:\n%s', vk_prod)
            self.products.append(vk_prod)
        logger.debug('создал объект класса ответа ВК на запрос всех товаров сообщества')
        logger.debug('количество товаров в ответе count - %d', self.count)
        logger.debug('количество товаров в ответе len(items) - %d', len(items))
        logger.debug('количество товаров количество товаров, которое загрузил - %d', len(self.products))

    def get_all_skus(self) -> list[str]:
        return [product.sku for product in self.products]

    def get_skus_id_dict(self) -> dict[str:str]:
        logger.debug('формирую словарь штрихкод: вк id')
        d = {product.sku: product.id for product in self.products}
        logger.debug('количество товаров в словаре - %d', len(d))
        return d
