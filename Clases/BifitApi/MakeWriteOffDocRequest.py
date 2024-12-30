from datetime import timezone, datetime, timedelta

from Clases.BifitApi.Request import Request


class MakeWriteOffDocRequest(Request):
    def __init__(self,
                 url: str,
                 token: str,
                 org_id: str,
                 trade_obj_id: str,
                 postings,
                 products) -> None:
        super().__init__()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        self.url = url

        tz = timezone(timedelta(hours=3))
        now = datetime.now(tz)
        timestamp = int(now.timestamp())
        current_time_ms = str(timestamp * 1000)

        self.data = {
            "document": {
                "id": None,
                "visible": True,
                "created": current_time_ms,
                "changed": current_time_ms,
                "organizationId": org_id,
                "tradeObjectId": trade_obj_id,
                "documentDate": current_time_ms,
                "status": "NEW",
                "responsiblePerson": "Легостаева Анастасия",
                "documentNumber": None,
                "description": None,
                "relatedDocuments": [],
                "writeOffArticleId": None,
                "contractorId": None,
                "purchaseAmount": None,
                "sellingAmount": None,
                "automatically": False
            },
            "items": [
                # {
                #     "id": None,
                #     "documentId": None,
                #     "nomenclatureId": 31195950,
                #     "vendorCode": "ali-vk-oz-ya",
                #     "barcode": "4673722702512",
                #     "unitCode": "796",
                #     "purchasePrice": 220.5,
                #     "sellingPrice": 420,
                #     "amount": 220.5,
                #     "currencyCode": None,
                #     "nomenclatureFeatures": [],
                #     "quantity": 0,
                #     "accountBalance": 2
                # }
            ]
        }


