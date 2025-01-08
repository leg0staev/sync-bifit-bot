class Nomenclature:
    __slots__ = (
        'id', 'organization_id', 'external_id', 'external_code', 'created', 'changed', 'barcode', 'vendor_code', 'name',
        'short_name', 'parent_id', 'vat_id', 'vat_value', 'unit_code', 'volume', 'capacity', 'capacity_unit_code',
        'purchase_price', 'selling_price', 'picture', 'weighted', 'grouped', 'focused', 'container', 'payment_subject',
        'adults_only', 'code', 'mark_type', 'gtin', 'plu_code', 'template', 'visible', 'contractor_activity_type',
        'contractor_id', 'custom', 'trade_object_relations', 'type', 'composite_goods', 'barcodes', 'country_code',
        'customs_declaration', 'description', 'pictures_ids', 'application', 'nomenclature_features',
        'org_member_points', 'global_nomenclature_id', 'quantum', 'global_category_id',
        'global_nomenclature_moderation_status', 'expiration', 'expiration_date', 'fifo', 'status', 'mark_up',
        'turnover', 'inventory_standard', 'countable', 'all_picture_ids', 'purchase_price_or_zero',
        'selling_price_or_zero', 'all_barcodes', 'external_id_without_prefix'
    )

    def __init__(self, data: dict) -> None:
        self.id = int(data.get("id", 0))
        self.organization_id = data.get("organizationId")
        self.external_id = data.get("externalId")
        self.external_code = data.get("externalCode")
        self.created = data.get("created")
        self.changed = data.get("changed")
        self.barcode = data.get("barcode")
        self.vendor_code = data.get("vendorCode")
        self.name = data.get("name")
        self.short_name = data.get("shortName")
        self.parent_id = data.get("parentId")
        self.vat_id = data.get("vatId")
        self.vat_value = data.get("vatValue")
        self.unit_code = data.get("unitCode")
        self.volume = data.get("volume")
        self.capacity = data.get("capacity")
        self.capacity_unit_code = data.get("capacityUnitCode")
        self.purchase_price = data.get("purchasePrice")
        self.selling_price = data.get("sellingPrice")
        self.picture = data.get("picture")
        self.weighted = data.get("weighted")
        self.grouped = data.get("grouped")
        self.focused = data.get("focused")
        self.container = data.get("container")
        self.payment_subject = data.get("paymentSubject")
        self.adults_only = data.get("adultsOnly")
        self.code = data.get("code")
        self.mark_type = data.get("markType", "UNKNOWN")
        self.gtin = data.get("gtin")
        self.plu_code = data.get("pluCode")
        self.template = data.get("template")
        self.visible = data.get("visible")
        self.contractor_activity_type = data.get("contractorActivityType")
        self.contractor_id = data.get("contractorId")
        self.custom = data.get("custom")
        self.trade_object_relations = data.get("tradeObjectRelations")
        self.type = data.get("type")
        self.composite_goods = data.get("compositeGoods")
        self.barcodes = data.get("barcodes")
        self.country_code = data.get("countryCode")
        self.customs_declaration = data.get("customsDeclaration")
        self.description = data.get("description")
        self.pictures_ids = data.get("picturesIds")
        self.application = data.get("application")
        self.nomenclature_features = data.get("nomenclatureFeatures")
        self.org_member_points = data.get("orgMemberPoints")
        self.global_nomenclature_id = data.get("globalNomenclatureId")
        self.quantum = data.get("quantum")
        self.global_category_id = data.get("globalCategoryId")
        self.global_nomenclature_moderation_status = data.get("globalNomenclatureModerationStatus")
        self.expiration = data.get("expiration")
        self.expiration_date = data.get("expirationDate")
        self.fifo = data.get("fifo")
        self.status = data.get("status")
        self.mark_up = data.get("markUp")
        self.turnover = data.get("turnover")
        self.inventory_standard = data.get("inventoryStandard")
        self.countable = data.get("countable")
        self.all_picture_ids = data.get("allPictureIds")
        self.purchase_price_or_zero = data.get("purchasePriceOrZero")
        self.selling_price_or_zero = data.get("sellingPriceOrZero")
        self.all_barcodes = data.get("allBarcodes")
        self.external_id_without_prefix = data.get("externalIdWithoutPrefix")

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Nomenclature) and self.id == other.id
