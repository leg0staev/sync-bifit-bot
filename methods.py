import base64
import hashlib

from Clases.BifitApi.TradeObjListReq import TradeObjListReq
from Clases.BifitApi.GoodsListReq import *
from Clases.BifitApi.AuthReq import *
from Clases.BifitApi.OrgListReq import *
from Clases.BifitApi.Organization import *
from Clases.BifitApi.TradeObject import *
from Clases.BifitApi.Good import *
from Clases.BifitApi.Goods import *
from Clases.BifitApi.Nomenclature import *
from Clases.ApiMarketplaces.Ya.YAapi import YAapi
from Clases.ApiMarketplaces.Ali.ALIapi import AliApi
from Clases.ApiMarketplaces.Vk.VkApi import VkApi
from Clases.ApiMarketplaces.Vk.VkProdResponce import VkProdResponse
from Clases.ApiMarketplaces.Ozon.OzonProdResponse import OzonProdResponse
from Clases.ApiMarketplaces.Ozon.OzonApi import OzonApi
from Clases.ApiMarketplaces.Ozon.Warehouse import Warehouse


def get_bifit_token(username: str, pswd: bytes) -> str:
    auth_json = AuthReq(username=username, password=pswd).send_post()
    return auth_json['access_token']


def get_bifit_org_list(token: str) -> list[Organization]:
    return [Organization(org) for org in OrgListReq(token=token).send_post()]


def get_bifit_trade_obj_list(token: str, org_id: str) -> list[TradeObject]:
    return [TradeObject(obj) for obj in TradeObjListReq(token=token, org_id=org_id).send_post()]


def get_bifit_products_list(token: str, org_id: str, obj_id: str) -> list[Good]:
    goods_list = GoodsListReq(token=token, org_id=org_id, trade_obj_id=obj_id).send_post()
    products = [Good(Goods(item['goods']), Nomenclature(item['nomenclature'])) for item in goods_list]
    return products


def get_markets_products(products_list: list[Good]) -> tuple[dict, dict, dict, dict]:
    ya_goods: dict[str:int] = {}
    ali_goods: dict[str:int] = {}
    vk_goods: dict[str:int] = {}
    ozon_goods: dict[str:int] = {}

    for product in products_list:
        try:
            markets: list[str] = product.nomenclature.vendor_code.split("-")
            # print(markets)
            if "ya" in markets:
                ya_goods[product.nomenclature.barcode] = product.goods.quantity
            if "oz" in markets:
                ozon_goods[product.nomenclature.barcode] = product.goods.quantity
            if "ali" in markets:
                ali_goods[product.nomenclature.barcode] = product.goods.quantity
            if "sber" in markets:
                pass
            if "vk" in markets:
                vk_goods[product.nomenclature.barcode] = product.goods.quantity
        except AttributeError:
            # print(f"Ошибка: товар {product.get_name()}")
            continue
    return ya_goods, ali_goods, vk_goods, ozon_goods


def get_encode(str_var: str) -> bytes:
    """
    функция кодирования пароля
    пароль -> SHA-256 -> base64
    """

    # перекодирование в формат UTF-8
    data = str_var.encode('utf-8')
    # вычисление хеша SHA-256
    hash_object = hashlib.sha256(data)
    hex_dig = hash_object.digest()
    # кодирование в base64
    base64_bytes = base64.b64encode(hex_dig)

    return base64_bytes


def send_to_yandex(ya_token: str,
                   ya_compaign_id: int,
                   ya_warehouse_id: int,
                   ya_goods_dict: dict[str:int]) -> dict:
    ya_api = YAapi(ya_token, ya_compaign_id, ya_warehouse_id, goods_dict=ya_goods_dict)
    ya_sand_remains_response = ya_api.send_remains()
    return ya_sand_remains_response


def send_to_ali(ali_token: str, ali_goods_dict: dict[str:int]) -> dict[str, str]:
    ali_api = AliApi(ali_token, ali_goods_dict)
    ali_api.fill_get_products_to_send()
    ali_sand_remains_response = ali_api.send_remains()
    return ali_sand_remains_response


def send_to_vk(vk_token: str, vk_owner_id: int, vk_api_ver: float, vk_goods_dict: dict[str:int]) -> dict:
    vk_api = VkApi(vk_token, vk_owner_id, vk_api_ver)
    vk_products_response = VkProdResponse(vk_api.get_all_products())
    vk_products_dict = vk_products_response.get_skus_id_dict()
    vk_sand_remains_response = vk_api.send_remains(vk_products_dict, vk_goods_dict)
    return vk_sand_remains_response


def send_to_ozon(ozon_admin_key: str, ozon_client_id: str, ozon_goods_dict: dict[str:int]):
    ozon_api = OzonApi(ozon_admin_key, ozon_client_id)
    ozon_products_response = OzonProdResponse(ozon_api.get_all_products())
    ozon_products_dict = ozon_products_response.get_skus_id_dict()
    ozon_warehouses = [Warehouse(w) for w in ozon_api.get_warehouses()['result'] if w['status'] != "disabled"]
    ozon_send_remains_response = ozon_api.send_remains(ozon_products_dict, ozon_goods_dict, ozon_warehouses)
    return ozon_send_remains_response
