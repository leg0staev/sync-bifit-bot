class AliSku:
    def __init__(self, data):
        self.id = data['id']
        self.sku_id = data['sku_id']
        self.code = data['code']
        self.price = data['price']
        self.discount_price = data['discount_price']
        self.ipm_sku_stock = data['ipm_sku_stock']
