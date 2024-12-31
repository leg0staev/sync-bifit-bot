from datetime import timezone, datetime, timedelta

from Clases.BifitApi.Request import Request


class MakeWriteOffDocRequest(Request):
    def __init__(self,
                 url: str,
                 token: str,
                 org_id: str,
                 trade_obj_id: str,
                 doc_num: str,
                 items: list[dict],
                 params: dict) -> None:
        super().__init__()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'Accept': '*/*'
        }
        self.url = f'{url}/protected/{org_id}/write_off_document'

        self.query_params = params

        tz = timezone(timedelta(hours=3))
        now = datetime.now(tz)
        timestamp = int(now.timestamp())
        current_time_ms = str(timestamp * 1000)

        self.json = {
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
                "documentNumber": doc_num,
                "description": None,
                "relatedDocuments": [],
                "writeOffArticleId": None,
                "contractorId": None,
                "purchaseAmount": None,
                "sellingAmount": None,
                "automatically": False
            },
            "items": items
        }


