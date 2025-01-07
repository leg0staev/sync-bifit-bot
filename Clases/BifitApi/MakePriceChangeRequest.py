from datetime import timezone, datetime, timedelta

from Clases.BifitApi.Request import Request


class MakePriceChangeRequest(Request):
    def __init__(self,
                 url: str,
                 token: str,
                 org_id: str,
                 trade_obj_id: str,
                 items: list[dict]) -> None:
        super().__init__()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'Accept': '*/*'
        }

        self.url = url

        tz = timezone(timedelta(hours=3))
        now = datetime.now(tz)
        timestamp = int(now.timestamp())
        current_time_ms = str(timestamp * 1000)

        self.json = {
            "document": {
                "id": None,
                "organizationId": org_id,
                "documentNumber": None,
                "tradeObjectId": trade_obj_id,
                "description": None,
                "responsibleUserId": None,
                "visible": True,
                "created": current_time_ms,
                "changed": current_time_ms,
                "priceChangeTime": current_time_ms,
                "status": "NEW",
                "relatedDocuments": []
            },
            "items": items
        }
