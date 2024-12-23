class TradeObject:
	"""Класс торгового объекта Бифит-кассы"""

	def __init__(self, data):
		self.id = data.get('id')
		self.created = data.get('created')
		self.changed = data.get('changed')
		self.organizationId = data.get('organizationId')
		self.name = data.get('name')
		self.address = data.get('address')
		self.taxSystemMask = data.get('taxSystemMask')
		self.taxSystemList = data.get('taxSystemList')
		self.kpp = data.get('kpp')
		self.application = data.get('application')
		self.mdlp = data.get('mdlp')


