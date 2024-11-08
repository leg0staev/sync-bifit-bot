"""
Бот синхронизации склада Бифит-кассы со складами маркетплэйсов.
"""
import asyncio
import threading

# from logger import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from Exceptions.ResponseContentException import ResponseContentException
from Exceptions.ResponseStatusException import ResponseStatusException
from bifit_session import bifit_session
from fastapi_app.app import app
from methods import parse_calculation, get_write_off_msg, products_write_off, \
    goods_list_to_csv_str
from methods_async import *
from settings import YA_TOKEN, YA_CAMPAIGN_ID, YA_WHEREHOUSE_ID, ALI_TOKEN, VK_TOKEN, VK_OWNER_ID, VK_API_VER, \
    OZON_CLIENT_ID, OZON_ADMIN_KEY, BOT_TOKEN


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Старт бота, инициализация, получение токена и данных по организации"""
    logger.debug("Старт бота, иницализация")
    await update.message.reply_text("tap /sync")
    logger.debug("Старт бота, иницализация - успех")


async def write_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает процесс списания товаров из склада бифит-кассы"""
    logger.debug("write_off started")
    calculation = update.message.text
    await update.message.reply_text("это что рассчет? сейчас проверю..")

    products_to_remove, without_barcode, without_quantity = parse_calculation(calculation)

    if not any((products_to_remove, without_barcode, without_quantity)):
        await update.message.reply_text("ты что то не то прислал..")
        return None

    if not products_to_remove:
        await update.message.reply_text("похоже твой рассчет без штрихколов "
                                        "или ты забыл указать количество. "
                                        " ничего списать не могу")
        return None

    message = get_write_off_msg(products_to_remove, without_barcode, without_quantity)

    await update.message.reply_text(message)
    await update.message.reply_text("сейчас запрошу актуальные остатки из Бифит")
    *_, goods_set = await bifit_session.get_bifit_products_async()
    if goods_set is None:
        await update.message.reply_text(f"не получил список товаров от Бифит. ошибка.")
        return None

    await update.message.reply_text("получил товары из Бифит, минусую.")
    updated_goods_set, outdated_goods_set = products_write_off(goods_set, products_to_remove)
    if updated_goods_set:
        csv_str = goods_list_to_csv_str(updated_goods_set)
        send_result = await bifit_session.send_csv_stocks(csv_str)
        if not send_result:
            await update.message.reply_text(f"Какая-то ошибка на этапе отправки корректных "
                                            f"остатков на сервер Бифит. Надо читать логи. "
                                            f"Напиши разработчику")
            return None
        await update.message.reply_text("Отправил остатки на сервер Бифит.\n"
                                        "Сообщения об ошибке:\n"
                                        f"{send_result.get('exceptionMessage')}\n"
                                        f"Список ошибок:\n"
                                        f"{send_result.get('exceptionList')}\n"
                                        f"Количество списанных товаров: "
                                        f"{send_result.get('itemQty')}")
    if outdated_goods_set:
        await update.message.reply_text('**ВНИМАНИЕ!** не смог списать, потому что не '
                                        'нашел такие штрих коды в базе Бифит. '
                                        'Отправь фото эих товаров @c0m_a, чтобы '
                                        'он списал вручную!\n'
                                        f'{outdated_goods_set}')


async def sync(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает процесс полной синхронизации всех маркетплэйсов со складом бифит-кассы"""

    try:
        ya_goods, ali_goods, vk_goods, ozon_goods, *_ = await bifit_session.get_bifit_products_async()
    except ResponseStatusException:
        await update.message.reply_text(f"не получил список товаров от Бифит. ошибка статуса сервера."
                                        f" тапни /sync чтобы попробовать еще раз")
        return None
    except ResponseContentException:
        await update.message.reply_text(f"не получил список товаров от Бифит. Неожиданный ответ сервера."
                                        f" тапни /sync чтобы попробовать еще раз")
        return None

    await update.message.reply_text("получил товары из бифит")

    coroutines = []

    if ya_goods:
        await update.message.reply_text("Нашел товары для Яндекс")
        coroutines.append(send_to_yandex_async(YA_TOKEN, YA_CAMPAIGN_ID, YA_WHEREHOUSE_ID, ya_goods))

    if ozon_goods:
        await update.message.reply_text("Нашел товары для Озон")
        coroutines.append(send_to_ozon_async(OZON_ADMIN_KEY, OZON_CLIENT_ID, ozon_goods))

    if ali_goods:
        await update.message.reply_text("Нашел товары для Ali")
        coroutines.append(send_to_ali_async(ALI_TOKEN, ali_goods))

    if vk_goods:
        await update.message.reply_text("Нашел товары для ВК")
        coroutines.append(send_to_vk_async(VK_TOKEN, VK_OWNER_ID, VK_API_VER, vk_goods))

    if coroutines:
        await update.message.reply_text("Отправляю все остатки")
        errors = await asyncio.gather(*coroutines)
        if any(errors):
            await update.message.reply_text("возникли ошибки при отправке данных:\n"
                                            "{Яндекс}, {Озон}, {Али}, {Вк}"
                                            f"{errors}")
        else:
            await update.message.reply_text("Отправка прошла без ошибок!")
    else:
        await update.message.reply_text("Нет товаров для отправки.")


async def synchronization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает процесс полной синхронизации всех маркетплэйсов со складом бифит-кассы"""

    market_prod_dict = await bifit_session.get_bifit_prod_by_markers(("ya", "oz", "ali", "vk"))

    if market_prod_dict:

        await update.message.reply_text("получил товары из бифит")

        ya_goods: dict[str, int] = market_prod_dict.get('ya')
        ali_goods: dict[str, int] = market_prod_dict.get('ali')
        vk_goods: dict[str, int] = market_prod_dict.get('vk')
        ozon_goods: dict[str, int] = market_prod_dict.get('oz')

        coroutines = set()

        if ya_goods:
            await update.message.reply_text("Нашел товары для Яндекс")
            coroutines.add(send_to_yandex_async(YA_TOKEN, YA_CAMPAIGN_ID, YA_WHEREHOUSE_ID, ya_goods))

        if ozon_goods:
            await update.message.reply_text("Нашел товары для Озон")
            coroutines.add(send_to_ozon_async(OZON_ADMIN_KEY, OZON_CLIENT_ID, ozon_goods))

        if ali_goods:
            await update.message.reply_text("Нашел товары для Ali")
            coroutines.add(send_to_ali_async(ALI_TOKEN, ali_goods))

        if vk_goods:
            await update.message.reply_text("Нашел товары для ВК")
            coroutines.add(send_to_vk_async(VK_TOKEN, VK_OWNER_ID, VK_API_VER, vk_goods))

        if coroutines:
            await update.message.reply_text("Отправляю все остатки")
            errors = await asyncio.gather(*coroutines)
            if any(errors):
                await update.message.reply_text("возникли ошибки при отправке данных:\n"
                                                "{Яндекс}, {Озон}, {Али}, {Вк}"
                                                f"{errors}")
            else:
                await update.message.reply_text("Отправка прошла без ошибок!")
    else:
        await update.message.reply_text(f"не получил список товаров от Бифит. ошибка"
                                        f" тапни /sync чтобы попробовать еще раз")
        return None


async def get_yab_pic_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выводит в бот ожидаемые ссылки на картинки"""

    products_response = await bifit_session.get_bifit_prod_by_markers(('yab',))

    yab_products_list = await bifit_session.get_yab_goods(products_response.get('yab'))

    for item in yab_products_list:
        product = item.get('good')
        vendor = item.get('vendor')

        pic_url = await get_pic_url(product.nomenclature.short_name, vendor.short_name, to_bot=True)
        await update.message.reply_text(f"товар {str(product)}: картинка - {pic_url}")


async def get_new_yml(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает процесс обновления YML которая находится в сессии"""
    await update.message.reply_text('Запускаю процесс обновления YML')
    yml_update_errors = await bifit_session.get_yml_async()

    if yml_update_errors:
        message = ''
        for product, error in yml_update_errors:
            message += f'для товара {product} {error}'
        await update.message.reply_text(message)
    else:
        await update.message.reply_text('YML обновлен без ошибок')


async def main_async() -> None:
    """Старт бота"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pic_links", get_yab_pic_names))
    application.add_handler(CommandHandler("get_yml", get_new_yml))
    application.add_handler(CommandHandler("sync", synchronization))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, write_off))
    # on non command i.e message - echo the message on Telegram
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Ожидаем завершения работы бота
    await asyncio.Event().wait()


async def initialize_session(session):
    while True:
        await session.initialize()
        await asyncio.sleep(12*60*60)


def run_uvicorn(bifit_session):
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main_bot(bifit_session):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_async())


if __name__ == "__main__":
    asyncio.run(initialize_session(bifit_session))

    uvicorn_thread = threading.Thread(target=run_uvicorn, args=(bifit_session,))
    uvicorn_thread.start()

    bot_thread = threading.Thread(target=main_bot, args=(bifit_session,))
    bot_thread.start()

    uvicorn_thread.join()
    bot_thread.join()
