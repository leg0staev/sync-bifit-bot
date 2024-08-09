class TradeObject:
	def __init__(self, data):
		self.id = data['id']
		self.created = data['created']
		self.changed = data['changed']
		self.organizationId = data['organizationId']
		self.name = data['name']
		self.address = data['address']
		self.taxSystemMask = data['taxSystemMask']
		self.taxSystemList = data['taxSystemList']
		self.kpp = data['kpp']
		self.application = data['application']
		self.mdlp = data['mdlp']

