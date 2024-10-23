from fastapi import FastAPI, Response
from Clases.BifitApi.Good import Good

from bifit_session import bifit_session
from methods import get_yab_categories

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/yml")
async def get_yml():
    products_set_response = await bifit_session.get_bifit_products_set_async()
    products_set: set[Good] = products_set_response[4]
    category_dict = await bifit_session.get_yab_categories_dict(products_set)


    categories_content = ''

    content = """<?xml version="1.0" encoding="UTF-8"?>
<yml_catalog date="2020-11-22T14:37:38+03:00">
    <shop>
        <name>pronogti.store</name>
        <company>pronogti.store</company>
        <currencies>
            <currency id="RUR" rate="1"/>
        </currencies>
        <categories>
        </categories>
    </shop>
</yml_catalog>"""
    return Response(content=content, media_type="application/xml")
