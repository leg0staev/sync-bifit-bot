class Organization:

    __slots__ = (
        'id', 'visible', 'created', 'name', 'address', 'inn',
        'taxSystemMask', 'taxSystemList', 'sla', 'receiptPriceLimit',
        'totalPriceLimit', 'permissions', 'email', 'phone', 'kpp',
        'economicActivityCode', 'region', 'fpId', 'defaultVat',
        'multiOrganization', 'internalType', 'organizationPostfix',
        'blocked', 'blockedCause'
    )

    def __init__(self, data):
        self.id = data.get('id')
        self.visible = data.get('visible')
        self.created = data.get('created')
        self.name = data.get('name')
        self.address = data.get('address')
        self.inn = int(data.get('inn'))
        self.taxSystemMask = data.get('taxSystemMask')
        self.taxSystemList = data.get('taxSystemList')
        self.sla = data.get('sla')
        self.receiptPriceLimit = data.get('receiptPriceLimit')
        self.totalPriceLimit = data.get('totalPriceLimit')
        self.permissions = data.get('permissions')
        self.email = data.get('email')
        self.phone = data.get('phone')
        self.kpp = data.get('kpp')
        self.economicActivityCode = data.get('economicActivityCode')
        self.region = data.get('region')
        self.fpId = data.get('fpId')
        self.defaultVat = data.get('defaultVat')
        self.multiOrganization = data.get('multiOrganization')
        self.internalType = data.get('internalType')
        self.organizationPostfix = data.get('organizationPostfix')
        self.blocked = data.get('blocked')
        self.blockedCause = data.get('blockedCause')
