class OzonProduct:
    __slots__ = (
        'product_id',
        'offer_id',
        'is_fbo_visible',
        'is_fbs_visible',
        'archived',
        'is_discounted',
    )

    def __init__(self, data: dict) -> None:
        self.product_id = int(data.get('product_id'))
        self.offer_id = data.get('offer_id')
        self.is_fbo_visible = data.get('is_fbo_visible')
        self.is_fbs_visible = data.get('is_fbs_visible')
        self.archived = data.get('archived')
        self.is_discounted = data.get('is_discounted')

    def __repr__(self) -> str:
        return f'OzonProduct(product_id={self.product_id}, offer_id={self.offer_id})'
