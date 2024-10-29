from datetime import datetime, timezone, timedelta

from Clases.BifitApi.Contactor import Contactor
from Clases.BifitApi.Good import Good
from Clases.BifitApi.Nomenclature import Nomenclature
from bifit_session import bifit_session
from fastapi import FastAPI, Response
from logger import logger

app = FastAPI()
tz = timezone(timedelta(hours=3))


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/yml")
async def get_yml():
    logger.debug(f'get_yml started')
    current_time = datetime.now(tz)

    products_set_response = await bifit_session.get_bifit_products_async()

    products_list: list[Good] = products_set_response[4]
    products_dict: dict[Good, Nomenclature] = await bifit_session.get_yab_goods(products_list)
    vendors_dict: dict[int, Contactor] = await bifit_session.get_vendors_async()

    categories_content = ''
    offers_content = ''

    categories = set(products_dict.values())
    for category in categories:
        categories_content += f'<category id="{category.id}">{category.name}</category>\n'

    for product, nomenclature in products_dict.items():
        available = 'true' if product.goods.quantity > 0 else 'false'
        offers_content += f"""<offer id="{product.nomenclature.id}"  available="{available}">
                <name>{product.nomenclature.name}</name>
                <price>{product.nomenclature.selling_price}</price>
                <currencyId>RUR</currencyId>
                <categoryId>{nomenclature.id}</categoryId>
                <picture>URL</picture>
                <delivery>true</delivery>
                <pickup>true</pickup>
                <description>
                    <![CDATA[
                        {product.nomenclature.description}
                    ]]>
                </description>
            </offer>"""
    logger.debug(f'{categories_content=}')

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<yml_catalog date="{current_time.isoformat()}">
    <shop>
        <name>pronogti.store</name>
        <company>pronogti.store</company>
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
