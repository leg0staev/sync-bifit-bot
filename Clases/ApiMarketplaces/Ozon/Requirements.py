class Requirements:

    __slots__ = (
        'products_requiring_gtd',
        'products_requiring_country',
        'products_requiring_mandatory_mark',
        'products_requiring_rnpt',
        'products_requiring_jw_uin',
    )

    def __init__(self, data: dict) -> None:
        self.products_requiring_gtd = data.get('products_requiring_gtd')
        self.products_requiring_country = data.get('products_requiring_country')
        self.products_requiring_mandatory_mark = data.get('products_requiring_mandatory_mark')
        self.products_requiring_rnpt = data.get('products_requiring_rnpt')
        self.products_requiring_jw_uin = data.get('products_requiring_jw_uin')
