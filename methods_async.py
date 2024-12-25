from transliterate import slugify

from Clases.ApiMarketplaces.Ali.AliApiAsync import AliApiAsync
from Clases.ApiMarketplaces.Ozon.OzonApiAsync import OzonApiAsync
from Clases.ApiMarketplaces.Ozon.OzonProdResponse import OzonProdResponse
from Clases.ApiMarketplaces.Ozon.Posting import Posting
from Clases.ApiMarketplaces.Ozon.Warehouse import Warehouse
from Clases.ApiMarketplaces.Vk.VkApiAsync import VkApiAsync
from Clases.ApiMarketplaces.Vk.VkProdResponce import VkProdResponse
from Clases.ApiMarketplaces.Ya.YAapiAsync import YAapiAsync
from Clases.BifitApi.Request import Request
from logger import logger


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
    logger.debug(f'send_to_yandex_async started')
    ya_api = YAapiAsync(ya_token, ya_campaign_id, ya_warehouse_id, goods_dict=ya_goods_dict)
    ya_send_remains_response = await ya_api.send_remains_async()
    if 'errors' in ya_send_remains_response:
        logger.error(f'ошибка на этапе отправки товаров в Яндекс - {ya_send_remains_response}')
        return ya_send_remains_response
    logger.debug(f'send_to_yandex_async finished smoothly')
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
    ozon_session = OzonApiAsync(ozon_admin_key, ozon_client_id)

    ozon_products_request = await ozon_session.get_all_products_async()
    logger.debug(f' ozon_products_request - {ozon_products_request}')
    if 'error' in ozon_products_request:
        logger.error(f'send_to_ozon_async finished with error - {ozon_products_request}')
        return ozon_products_request
    try:
        ozon_products_response = OzonProdResponse(ozon_products_request)
    except KeyError as e:
        logger.error(f'Ошибка в ответе сервера на запрос товаров Озон - {e}')
        return {'error': f'Ошибка в ответе сервера на запрос товаров Озон - {str(e)}'}
    ozon_products_dict = ozon_products_response.get_skus_id_dict()
    logger.debug(f' ozon_products_dict - {ozon_products_dict}')
    ozon_warehouses_response = await ozon_session.get_warehouses_async()
    logger.debug(f' ozon_warehouses_response - {ozon_warehouses_response}')
    warehouses_result_list = ozon_warehouses_response.get('result')
    if not warehouses_result_list:
        logger.error(f'Ошибка в ответе сервера на запрос списка складов Озон - {ozon_warehouses_response}')
        return {'error': f'Ошибка в ответе сервера на запрос списка складов - {ozon_warehouses_response}'}

    ozon_warehouses = [Warehouse(w) for w in warehouses_result_list if w.get('status') != "disabled"]
    return await ozon_session.send_remains_async(ozon_products_dict, ozon_goods_dict, ozon_warehouses)


async def make_write_off_docs_from_ozon(ozon_admin_key: str, ozon_client_id: str):
    ozon_session = OzonApiAsync(ozon_admin_key, ozon_client_id)
    ozon_postings_response = await ozon_session.get_all_postings_async()

    result = ozon_postings_response.get('result')
    if result is None:
        logger.error(f'Ошибка в ответе сервера на запрос отправлений Озон')
        return {'error': 'Ошибка в ответе сервера на запрос отправлений Озон - неожиданный ответ сервера'}

    ozon_postings = [Posting(item) for item in result.get('postings')]
    if not ozon_postings:
        return {'error': 'Ошибка, список отправлений пуст'}
    return ozon_postings

async def send_to_ali_async(ali_token: str, ali_goods_dict: dict[str:int]) -> dict:
    ali_api = AliApiAsync(ali_token, ali_goods_dict)
    err = await ali_api.fill_get_products_to_send()
    if err:
        return err
    return await ali_api.send_remains_async()


async def get_pic_url(pic_name: str, vendor_name: str, to_bot: bool = False) -> str:
    """Формирует ссылку на изображение товара"""
    logger.debug('get_pic_url started')
    my_site_url = 'https://pronogti.store'
    vendor_name = slugify(vendor_name, 'uk')
    pic_name = slugify(pic_name, 'uk')
    pic_url = f'{my_site_url}/images/{vendor_name}/{pic_name}.jpg'
    if to_bot:
        return pic_url
    logger.debug('сформировал ссылку на картинку товара\n'
                 f'{pic_url=}. отправляю запрос')
    pic_request = Request(url=pic_url)
    pic_response = await pic_request.send_get_async()
    if 'error' in pic_response:
        logger.error('ERROR ошибка при получении изображения\n'
                     f'ставлю заглушку {my_site_url}/images/no-image.jpg\n'
                     'get_pic_url finished with exception')
        return f'{my_site_url}/images/no-image.jpg'
    logger.debug('ОК нашел картинку на сервере.\n'
                 'get_pic_url finished smoothly')
    return pic_url
