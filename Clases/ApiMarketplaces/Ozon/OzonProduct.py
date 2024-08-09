class OzonProduct:
    def __init__(self, data) -> None:
        self.product_id: int = data['product_id']
        self.offer_id: str = data['offer_id']
        self.is_fbo_visible: str = data['is_fbo_visible']
        self.is_fbs_visible: str = data['is_fbs_visible']
        self.archived: str = data['archived']
        self.is_discounted: str = data['is_discounted']
