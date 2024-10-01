class Goods:
    def __init__(self, data: str):
        self.trade_trade_object_id = data['tradeObjectId']
        self.nomenclature_id = data['nomenclatureId']

        quantity = data.get('quantity', 0)

        if quantity < 0:
            self.quantity = 0
        else:
            self.quantity = int(quantity)

        self.changed = data.get('changed')

