from dataclasses import dataclass


@dataclass
class NomenclatureFeature:
    id: int
    nomenclatureId: int
    featureId: int
    value: str
    created: str
