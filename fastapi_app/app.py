from fastapi import FastAPI, Response


from bifit_session import bifit_session

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/yml")
async def get_yml():
    products_set = await bifit_session.get_bifit_products_set_async()
    content = """<?xml version="1.0" encoding="UTF-8"?>
<yml_catalog date="2020-11-22T14:37:38+03:00">
    <shop>
        <name>pronogti.store</name>
        <company>pronogti.store</company>
        <currencies>
            <currency id="RUR" rate="1"/>
        </currencies>"""
    return Response(content=content, media_type="application/xml")
