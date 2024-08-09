from Clases.ApiMarketplaces.Ali.AliApiAsync import AliApiAsync
from Clases.ApiMarketplaces.Ozon.OzonApiAsync import OzonApiAsync
from Clases.ApiMarketplaces.Ozon.OzonProdResponse import OzonProdResponse
from Clases.ApiMarketplaces.Ozon.Warehouse import Warehouse
from Clases.ApiMarketplaces.Vk.VkApiAsync import VkApiAsync
from Clases.ApiMarketplaces.Vk.VkProdResponce import VkProdResponse
from Clases.ApiMarketplaces.Ya.YAapiAsync import YAapiAsync
from Clases.BifitApi.AuthReq import *
from Clases.BifitApi.Good import Good
from Clases.BifitApi.Goods import Goods
from Clases.BifitApi.GoodsListReq import GoodsListReq
from Clases.BifitApi.Nomenclature import Nomenclature
from Clases.BifitApi.OrgListReq import *
from Clases.BifitApi.Organization import *
from Clases.BifitApi.TradeObjListReq import *
from Clases.BifitApi.TradeObject import TradeObject
from logger import logger


async def get_bifit_token_async(login: str, password: str) -> str | None:
    logger.debug('get_bifit_token_async started')
    auth_req = AuthReq(username=login, password=password)
    auth_json = await auth_req.send_post_async()

    if 'error' in auth_json:
        logger.error(f'Ошибка на этапе запроса токена - {auth_json}')
        return None

    bifit_tok = auth_json.get('access_token')

    if bifit_tok is not None:
        logger.debug('get_bifit_token_async finished smoothly')
        return bifit_tok

    logger.error('В ответе сервера нет ключа access_token.')
    logger.debug('get_bifit_token_async finished with exception')
    return None


async def get_first_bifit_org_async(token: str) -> Organization | None:
    logger.debug('get_bifit_org_list_async started')
    org_list_request = OrgListReq(token=token)
    org_list_response = await org_list_request.send_post_async()

    if 'error' in org_list_response:
        logger.error(f'Ошибка на этапе запроса списка организаций - {org_list_response}')
        return None
    try:
        org_list = [Organization(org) for org in org_list_response]
        logger.debug('get_bifit_org_list_async finished smoothly')
        return org_list[0]
    except KeyError as e:
        logger.error(f'Ошибка формирования списка организаций - {e}')
        logger.debug('get_bifit_org_list_async finished with exception')
        return None


async def get_first_bifit_trade_obj_async(token: str, org_id: str) -> TradeObject | None:
    logger.debug('get_bifit_org_list_async started')
    trade_obj_list_request = TradeObjListReq(token=token, org_id=org_id)
    trade_obj_list_response = await trade_obj_list_request.send_post_async()

    if 'error' in trade_obj_list_response:
        logger.error(f'Ошибка на этапе запроса списка организаций - {trade_obj_list_response}')
        return None
    try:
        trade_obj_list = [TradeObject(obj) for obj in trade_obj_list_response]
        logger.debug('get_bifit_org_list_async finished smoothly')
        return trade_obj_list[0]
    except KeyError as e:
        logger.error(f'Ошибка формирования списка торговых объектов - {e}')
        logger.debug('get_bifit_org_list_async finished with exception')
        return None


async def get_bifit_products_list_async(token: str, org_id: str, obj_id: str) -> list[Good] | None:
    logger.debug('get_bifit_products_list_async started')
    goods_list_request = GoodsListReq(token=token, org_id=org_id, trade_obj_id=obj_id)
    goods_list_response = await goods_list_request.send_post_async()
    if 'error' in goods_list_response:
        logger.error(f'Ошибка на этапе запроса списка товаров - {goods_list_response}')
        return None
    try:
        products = [Good(Goods(item['goods']), Nomenclature(item['nomenclature'])) for item in goods_list_response]
        logger.debug('get_bifit_products_list_async finished smoothly')
        return products
    except KeyError as e:
        logger.error(f'Ошибка формирования списка товаров - {e}')
        logger.debug('get_bifit_products_list_async finished with exception')
        return None


async def send_to_yandex_async(ya_token: str,
                               ya_campaign_id: int,
                               ya_warehouse_id: int,
                               ya_goods_dict: dict[str, int]) -> dict:
    """
    Отправляет данные об остатках товаров на складе в Яндекс.Маркет.

    :param ya_token: токен для доступа к API Яндекс.Маркета
    :param ya_campaign_id: идентификатор кампании в Яндекс.Маркете
    :param ya_warehouse_id: идентификатор склада в Яндекс.Маркете
    :param ya_goods_dict: словарь с SKU товаров и их количеством
    :return: словарь с ответом сервера, в случае с ошибки или пустой словарь, если ошибок нет
    """
    ya_api = YAapiAsync(ya_token, ya_campaign_id, ya_warehouse_id, goods_dict=ya_goods_dict)
    ya_send_remains_response = await ya_api.send_remains_async()
    if 'errors' in ya_send_remains_response:
        logger.error(f'ошибка на этапе отправки товаров в Яндекс - {ya_send_remains_response}')
        return ya_send_remains_response
    return {}


async def send_to_vk_async(vk_token: str,
                           vk_owner_id: int,
                           vk_api_ver: float,
                           vk_goods_dict: dict[str, int]) -> dict:
    logger.debug('send_to_vk_async started')
    vk_api = VkApiAsync(vk_token, vk_owner_id, vk_api_ver)
    vk_products_response = await vk_api.get_all_products_async()
    if 'error' in vk_products_response:
        logger.error(f'ошибка на этапе запроса товаров в ВК - {vk_products_response}')
        return vk_products_response
    try:
        vk_response = VkProdResponse(vk_products_response)
    except KeyError as e:
        logger.error(f'Ошибка в ответе сервера на запрос товаров ВК - {e}')
        logger.debug('send_to_vk_async finished with exception')
        return {'error': f'Ошибка в ответе сервера на запрос товаров ВК - {str(e)}'}
    vk_products_dict = vk_response.get_skus_id_dict()
    logger.debug('send_to_vk_async finished smoothly')
    return await vk_api.send_remains_async(vk_products_dict, vk_goods_dict)


async def send_to_ozon_async(ozon_admin_key: str, ozon_client_id: str, ozon_goods_dict: dict[str:int]) -> dict:
    ozon_api = OzonApiAsync(ozon_admin_key, ozon_client_id)
    ozon_products_request = await ozon_api.get_all_products_async()
    logger.debug(f' ozon_products_request - {ozon_products_request}')
    if 'error' in ozon_products_request:
        logger.error(f'send_to_ozon_async finished with error - {ozon_products_request}')
        return ozon_products_request
    try:
        ozon_products_response = OzonProdResponse(ozon_products_request)
    except KeyError as e:
        logger.error(f'Ошибка в ответе сервера на запрос товаров Озон - {e}')
        return {'error': f'Ошибка в ответе сервера на запрос товаров ВК - {str(e)}'}
    ozon_products_dict = ozon_products_response.get_skus_id_dict()
    logger.debug(f' ozon_products_dict - {ozon_products_dict}')
    ozon_warehouses_response = await ozon_api.get_warehouses_async()
    logger.debug(f' ozon_warehouses_response - {ozon_warehouses_response}')
    warehouses_result_list = ozon_warehouses_response.get('result')
    if not warehouses_result_list:
        logger.error(f'Ошибка в ответе сервера на запрос списка складов Озон - {ozon_warehouses_response}')
        return {'error': f'Ошибка в ответе сервера на запрос списка складов - {ozon_warehouses_response}'}

    ozon_warehouses = [Warehouse(w) for w in warehouses_result_list if w.get('status') != "disabled"]
    return await ozon_api.send_remains_async(ozon_products_dict, ozon_goods_dict, ozon_warehouses)


async def send_to_ali_async(ali_token: str, ali_goods_dict: dict[str:int]) -> dict:
    ali_api = AliApiAsync(ali_token, ali_goods_dict)
    err = await ali_api.fill_get_products_to_send()
    if err:
        return err
    return await ali_api.send_remains_async()
