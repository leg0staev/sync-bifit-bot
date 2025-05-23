from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, Response

from Clases.BifitApi.Contactor import Contactor
from sessions import bifit_session
from logger import logger
from methods.methods_async import get_pic_url

app = FastAPI()
tz = timezone(timedelta(hours=3))


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/yml_old")
async def get_yml():
    logger.debug(f'get_yml started')
    current_time = datetime.now(tz)

    products_response = await bifit_session.get_bifit_prod_by_marker(('yab',))

    yab_products_list = await bifit_session.get_yab_goods_list(products_response.get('yab'))

    categories_content = ''
    offers_content = ''

    categories = set()

    for item in yab_products_list:
        product = item.get('good')
        vendor = item.get('vendor') or Contactor({'shortName': 'n0 vendor'})
        category = item.get('parent_nomenclature')

        categories.add(category)

        available = 'true' if product.goods.quantity > 0 else 'false'
        pic_url = await get_pic_url(product.nomenclature.short_name, vendor.short_name)

        offers_content += f"""<offer id="{product.nomenclature.id}"  available="{available}">
                    <name>{product.nomenclature.name}</name>
                    <vendor>{vendor.short_name}</vendor>
                    <price>{product.nomenclature.selling_price}</price>
                    <currencyId>RUR</currencyId>
                    <categoryId>{category.id}</categoryId>
                    <picture>{pic_url}</picture>
                    <description>
                        <![CDATA[
                            {product.nomenclature.description}
                        ]]>
                    </description>
                </offer>"""

    for category in categories:
        categories_content += f'<category id="{category.id}">{category.name}</category>\n'

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<yml_catalog date="{current_time.isoformat()}">
    <shop>
        <name>pronogti.store</name>
        <company>pronogti.store</company>
        <url>https://pronogti.store</url>
        <currencies>
            <currency id="RUR" rate="1"/>
        </currencies>
        <categories>
            {categories_content.strip()}
        </categories>
        <offers>
            {offers_content}
        </offers>
    </shop>
</yml_catalog>"""
    return Response(content=content, media_type="application/xml")


@app.get("/yml")
async def get_yml_from_session():
    logger.debug(f'get_yml_from_session started')
    yml = bifit_session.yml_str
    return Response(content=yml, media_type="application/xml")
