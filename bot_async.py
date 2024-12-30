"""
Бот синхронизации склада Бифит-кассы со складами маркетплэйсов.
"""
import asyncio
import threading

import uvicorn
# from logger import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from fastapi_app.app import app
from methods import *
from methods_async import *
from sessions import bifit_session
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
    logger.debug(f'получено сообщение - {calculation}')
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
    await update.message.reply_text("отправляю запрос на актуальные остатки из Бифит")

    server_response = await bifit_session.get_all_bifit_prod_response()
    if 'error' in server_response:
        await update.message.reply_text(f"сервер вернул ошибку - {server_response.get('error')}")
        return None
    await update.message.reply_text(f"получил ответ от сервера, пробую прочитать")

    goods_set = get_bifit_products_set(server_response)
    if 'error' in goods_set:
        await update.message.reply_text(f"не могу прочитать товары. неожиданный ответ сервера")
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


async def synchronization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает процесс полной синхронизации всех маркетплэйсов со складом бифит-кассы"""

    market_prod_dict = await bifit_session.get_bifit_prod_by_marker(("ya", "oz", "ali", "vk"))

    if 'error' in market_prod_dict:
        await update.message.reply_text(f"не получил список товаров от Бифит. ошибка"
                                        f" тапни /sync чтобы попробовать еще раз")
        return None

    else:
        await update.message.reply_text("получил товары из бифит")

        ya_goods: dict[str, int] = get_market_goods_dict(market_prod_dict.get('ya'))
        ali_goods: dict[str, int] = get_market_goods_dict(market_prod_dict.get('ali'))
        vk_goods: dict[str, int] = get_market_goods_dict(market_prod_dict.get('vk'))
        ozon_goods: dict[str, int] = get_market_goods_dict(market_prod_dict.get('oz'))

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


async def get_yab_pic_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выводит в бот ожидаемые ссылки на картинки 15 последних измененных товаров"""
    TAIL = -15

    products_response = await bifit_session.get_bifit_prod_by_marker(('yab',))

    yab_products_list = await bifit_session.get_yab_goods_list(products_response.get('yab'))

    last_changed_list = yab_products_list[TAIL:]

    message = f'ссылки на картинки {TAIL} последних измененных товара:\n'

    for item in last_changed_list:
        product = item.get('good')
        vendor = item.get('vendor')

        pic_url = await get_pic_url(product.nomenclature.short_name, vendor.short_name, to_bot=True)

        message += f"{str(product)}: картинка - {pic_url}\n"

    await update.message.reply_text(message)


async def get_new_yml(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает процесс обновления YML которая находится в сессии"""
    await update.message.reply_text('Запускаю процесс обновления YML')
    yml_update_errors = await bifit_session.get_yml_async()

    if yml_update_errors:
        message = ''
        for product, error in yml_update_errors.items():
            message += f'для товара {product} - {error}'
        await update.message.reply_text(message)
    else:
        await update.message.reply_text('YML обновлен без ошибок')


async def make_write_off_docs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создает документы списания исходя из заказов на маркетах"""
    await update.message.reply_text('запрашиваю отправления в ОЗОН и товары в Бифит')

    coroutines = set()
    ozon_session = OzonApiAsync(OZON_ADMIN_KEY, OZON_CLIENT_ID)
    # bifit_products = await bifit_session.get_bifit_prod_by_markers()
    # ozon_postings = await ozon_session.get_all_postings_async()
    coroutines.add(bifit_session.get_bifit_prod_by_marker(('oz',)))
    coroutines.add(ozon_session.get_all_postings_async())

    products, ozon_postings = await asyncio.gather(*coroutines)

    if 'error' in products:
        await update.message.reply_text(f'Ошибка от Бифит: {products.get("error")}')
        return None
    if 'error' in ozon_postings:
        await update.message.reply_text(f'Ошибка от Озон. не удалось запросить отправления')
        return None

    make_docs_resp = await bifit_session.make_ozon_write_off_doc_async(products.get('oz'), ozon_postings)

    if 'error' in make_docs_resp:
        await update.message.reply_text(f'не смог создать документ: {make_docs_resp.get("error")}')
        return None
    await update.message.reply_text(f'создал документы списания!')


async def keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просто пример клавиатуры))"""
    keyboard = [
        [InlineKeyboardButton("да, создать списание", callback_data='make_write_off_document')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('создать документы списания в бифит-касса?', reply_markup=reply_markup)


async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # Добавьте свою логику для make_document
    if data == 'make_write_off_document':
        await query.edit_message_text(text="хорошо, создаю списание")
        await make_write_off_document(update, context)


async def make_write_off_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Ваша логика для make_document
    await query.edit_message_text(text="Документы созданы!")


async def main_bot_async() -> None:
    """Старт бота"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pic_links", get_yab_pic_names))
    application.add_handler(CommandHandler("get_yml", get_new_yml))
    application.add_handler(CommandHandler("get_ozon_postings", make_write_off_docs))
    application.add_handler(CommandHandler("sync", synchronization))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, write_off))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
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
        await asyncio.sleep(12 * 60 * 60)


def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=8000)


def run_bot():
    asyncio.run(main_bot_async())


async def main():
    # Создание задачи для инициализации сессии
    session_task = asyncio.create_task(initialize_session(bifit_session))

    # Запуск Uvicorn в отдельном потоке
    uvicorn_thread = threading.Thread(target=run_uvicorn)
    uvicorn_thread.start()

    # Запуск основного асинхронного кода бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Ожидание завершения потока Uvicorn и бота
    await asyncio.to_thread(uvicorn_thread.join)
    await asyncio.to_thread(bot_thread.join)

    # Опционально: ожидание завершения задачи инициализации сессии
    await session_task


if __name__ == "__main__":
    asyncio.run(main())
