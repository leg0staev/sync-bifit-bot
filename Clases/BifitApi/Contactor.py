class Contactor:
    """Класс поставщика Бифит-кассы"""

    def __init__(self, data: dict) -> None:
        self.id = int(data.get("id"))
        self.organization_id = data.get("organizationId")
        self.external_id = data.get("externalId")
        self.external_code = data.get("externalCode")
        self.created = data.get("created")
        self.changed = data.get("changed")
        self.short_name = data.get("shortName")
        self.full_name = data.get("fullName")
        self.inn = data.get("inn")
        self.phone = data.get("phone")
        self.organization_phone = data.get("organizationPhone")
        self.email = data.get("email")
        self.address = data.get("address")
        self.group_types = data.get("groupTypes")
        self.activity_types = data.get("activityTypes")
        self.visible = data.get("visible")
        self.edi_identifier = data.get("ediIdentifier")
        self.reference_organization_id = data.get("referenceOrganizationId")
        self.delivery_schedule = data.get("deliverySchedule")
        self.has_price_list = data.get("hasPriceList")
        self.down_quantum_round = data.get("downQuantumRound")
        self.external_id_without_prefix = data.get("externalIdWithoutPrefix")

    def __str__(self) -> str:
        return f"Contactor(id={self.id}, short_name={self.short_name})"
