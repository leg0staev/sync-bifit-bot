from dataclasses import dataclass


@dataclass
class TradeObjectRelation:
    organizationId: str
    tradeObjectId: str
    nomenclatureId: int
    sellingPrice: int
    orgMemberPoints: int
    blocked: bool
