from Clases.ApiMarketplaces.Vk.Currency import Currency


class Price:
    def __init__(self, data) -> None:
        self.__amount = data['amount']
        self.__currency = Currency(data['currency'])
        self.__text = data['text']
        self.__price_type = data['price_type']
        self.__price_unit = data['price_unit']
        # self.__discount_rate = data['discount_rate']
        # self.__old_amount = data['old_amount']
        # self.__old_amount_text = data['old_amount_text']
