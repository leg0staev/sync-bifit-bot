class PostingProduct:
    """Класс продукта из которых состоит отправление Озон"""

    __slots__ = ('price', 'offer_id', 'name', 'sku', 'quantity', 'mandatory_mark', 'currency_code')

    def __init__(self, product_data: dict) -> None:
        self.price = product_data.get("price")
        self.offer_id = int(product_data.get("offer_id"))
        self.name = product_data.get("name")
        self.sku = product_data.get("sku")
        self.quantity = product_data.get("quantity")
        self.mandatory_mark = product_data.get("mandatory_mark", [])
        self.currency_code = product_data.get("currency_code")

    def __repr__(self) -> str:
        return f'Product(name="{self.name}", price={self.price}, offer_id={self.offer_id})'
