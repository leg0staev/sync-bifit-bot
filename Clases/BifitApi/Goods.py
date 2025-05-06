class Goods:
    def __init__(self, data: dict) -> None:
        """Класс товара"""
        self.trade_trade_object_id = data.get('tradeObjectId')
        self.nomenclature_id = int(data.get('nomenclatureId'))

        quantity = data.get('quantity', 0)

        if quantity < 0:
            self.quantity = 0
        else:
            self.quantity = int(quantity)

        self.changed = data.get('changed')

    def __repr__(self):
        return (f'trade_trade_object_id: {self.trade_trade_object_id},\n'
                f'nomenclature_id: {self.nomenclature_id},\n'
                f'quantity: {self.quantity}')


if __name__ == '__main__':
    goods = Goods({'nomenclatureId':0})
    print(goods)
