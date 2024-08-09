class Product:
    def __init__(self,
                 product_id: int,
                 product_name: str,
                 product_sku: str,
                 product_ali_id: str,
                 product_quantity: int):
        self.product_id = product_id
        self.product_name = product_name
        self.product_sku = product_sku
        self.product_ali_id = product_ali_id
        self.product_quantity = product_quantity
