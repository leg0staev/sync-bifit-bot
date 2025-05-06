from Clases.ApiMarketplaces.Vk.Currency import Currency


class Price:
    def __init__(self, data) -> None:
        self.amount = float(data['amount']) / 100
        self.currency = Currency(data['currency'])
        self.text = data['text']
        self.price_type = data['price_type']
        self.price_unit = data['price_unit']
        # self.__discount_rate = data['discount_rate']
        # self.__old_amount = data['old_amount']
        # self.__old_amount_text = data['old_amount_text']
