class DeliveryMethod:
    """
    Класс метода доставки OZON
    """
    __slots__ = "id", "name", "warehouse_id", "warehouse", "tpl_provider_id", "tpl_provider"

    def __init__(self, data: dict) -> None:
        self.id = data.get("id")
        self.name = data.get("name")
        self.warehouse_id = data.get("warehouse_id")
        self.warehouse = data.get("warehouse")
        self.tpl_provider_id = data.get("tpl_provider_id")
        self.tpl_provider = data.get("tpl_provider")

    def __str__(self) -> str:
        return f"Метод доставки - {self.name}, склад - {self.warehouse}"
