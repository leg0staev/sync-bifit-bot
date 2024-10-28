from fastapi import FastAPI, Response
from datetime import datetime, timezone, timedelta


from Clases.BifitApi.Good import Good

from bifit_session import bifit_session
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

    products_set_response = await bifit_session.get_bifit_products_set_async()

    products_set: set[Good] = products_set_response[4]

    category_dict = await bifit_session.get_yab_categories_dict(products_set)

    categories_content = ''
    for cat_name, cat_id in category_dict.items():
        categories_content += f'<category id="{cat_id}">{cat_name}</category>\n'
    logger.debug(f'{categories_content=}')

    offers_content = ''



    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<yml_catalog date="{current_time.isoformat()}">
    <shop>
        <name>pronogti.store</name>
        <company>pronogti.store</company>
        <currencies>
            <currency id="RUR" rate="1"/>
        </currencies>
        <categories>
        {categories_content}
        </categories>
        <offers>
            <offer id="9012">
                <name>Мороженица Brand 3811</name>
                <url>http://best.seller.ru/product_page.asp?pid=12345</url>
                <price>8990</price>
                <currencyId>RUR</currencyId>
                <categoryId>10</categoryId>
                <delivery>true</delivery>
                <delivery-options>
                    <option cost="300" days="1" order-before="18"/>
                </delivery-options>
                <param name="Цвет">белый</param>
                <weight>3.6</weight>
                <dimensions>20.1/20.551/22.5</dimensions>
            </offer>
        </offers>
    </shop>
</yml_catalog>"""
    return Response(content=content, media_type="application/xml")
