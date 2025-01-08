from dataclasses import dataclass


@dataclass
class CompositeGood:
    nomenclatureId: int
    parentId: int
    compositeType: str
    quantity: int
    linkId: int
    price: int
