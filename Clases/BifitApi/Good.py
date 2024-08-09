from Clases.BifitApi.Goods import *
from Clases.BifitApi.Nomenclature import *


class Good():
    def __init__(self, goods: Goods, nomenclature: Nomenclature):
        self.goods: Goods = goods
        self.nomenclature: Nomenclature = nomenclature
