from Clases.BifitApi.Goods import *
from Clases.BifitApi.Nomenclature import *


class Good():
    """Класс товара Бифит-кассы"""
    def __init__(self, goods: Goods, nomenclature: Nomenclature):
        self.goods: Goods = goods
        self.nomenclature: Nomenclature = nomenclature

    def __hash__(self):
        return hash(self.nomenclature.id)
