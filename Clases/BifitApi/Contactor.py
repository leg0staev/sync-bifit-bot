class Contactor:
    """Класс поставщика Бифит-кассы"""
    def __init__(self, data) -> None:
        self.id = data["id"]
        self.organization_id = data["organizationId"]
        self.external_id = data["externalId"]
        self.external_code = data["externalCode"]
        self.created = data["created"]
        self.changed = data["changed"]
        self.short_name = data["shortName"]
        self.full_name = data["fullName"]
        self.inn = data["inn"]
        self.phone = data["phone"]
        self.organization_phone = data["organizationPhone"]
        self.email = data["email"]
        self.address = data["address"]
        self.group_types = data["groupTypes"]
        self.activity_types = data["activityTypes"]
        self.visible = data["visible"]
        self.edi_identifier = data["ediIdentifier"]
        self.reference_organization_id = data["referenceOrganizationId"]
        self.delivery_schedule = data["deliverySchedule"]
        self.has_price_list = data["hasPriceList"]
        self.down_quantum_round = data["downQuantumRound"]
        self.external_id_without_prefix = data["externalIdWithoutPrefix"]

    def __str__(self) -> str:
        return f"Contactor(id={self.id}, short_name={self.short_name})"
