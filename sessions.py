from Clases.BifitApi.BifitSession import BifitSession
from Clases.ApiMarketplaces.Ozon.OzonApiAsync import OzonApiAsync

from settings import USERNAME, PASSWORD, OZON_ADMIN_KEY, OZON_CLIENT_ID

bifit_session = BifitSession(USERNAME, PASSWORD)
ozon_session = OzonApiAsync(OZON_ADMIN_KEY, OZON_CLIENT_ID)
