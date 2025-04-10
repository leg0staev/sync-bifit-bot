from Clases.BifitApi.Goods import *
from Clases.BifitApi.Nomenclature import *


class Good:
    """Класс товара Бифит-кассы"""
    def __init__(self, goods: Goods, nomenclature: Nomenclature) -> None:
        self.goods: Goods = goods
        self.nomenclature: Nomenclature = nomenclature

    def __hash__(self):
        return hash(self.nomenclature.id)

    def __eq__(self, other):
        return isinstance(other, Good) and self.nomenclature.id == other.nomenclature.id

    # def __str__(self):
    #     return f'{self.nomenclature.name}'

    def __repr__(self):
        return (f'товар - {self.nomenclature.name}\n'
                f'штрихкод - {self.nomenclature.barcode}\n'
                f'количество в кассе - {self.goods.quantity}')
