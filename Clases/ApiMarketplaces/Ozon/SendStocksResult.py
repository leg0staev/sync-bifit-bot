class SendStocksResult:
    def __init__(self,
                 warehouse_id: int,
                 product_id: int,
                 offer_id: str,
                 updated: bool,
                 errors: list) -> None:
        self.warehouse_id = warehouse_id
        self.product_id = product_id
        self.offer_id = offer_id
        self.updated = updated
        self.errors = errors

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def __repr__(self):
        return (f'SendRemainsResult(warehouse_id={self.warehouse_id}), product_id={self.product_id}, '
                f'offer_id={self.offer_id}, updated={self.updated}, errors={self.errors}')
