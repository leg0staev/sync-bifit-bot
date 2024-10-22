"""
Бот синхронизации склада Бифит-кассы со складами маркетплэйсов.
"""
import asyncio
import multiprocessing

import uvicorn
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
    """старт бота, инициализация, получение токена и данных по организации"""
    logger.debug("Старт бота, иницализация")
    await bifit_session.initialize()
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
    *_, goods_set = await bifit_session.get_bifit_products_set_async()
    if goods_set is None:
        await update.message.reply_text(f"не получил список товаров от Бифит. ошибка."
                                        f" тапни /sync чтобы попробовать еще раз")
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
        ya_goods, ali_goods, vk_goods, ozon_goods, *_ = await bifit_session.get_bifit_products_set_async()
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


async def main_async() -> None:
    """Старт бота"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sync", sync))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, write_off))
    # on non command i.e message - echo the message on Telegram
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Ожидаем завершения работы бота
    await asyncio.Event().wait()


def main_bot() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_async())


def run_uvicorn() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    # bot_thread = threading.Thread(target=main)
    # bot_thread.start()
    #
    # uvicorn.run(app, host="127.0.0.1", port=8000)

    uvicorn_process = multiprocessing.Process(target=run_uvicorn)
    uvicorn_process.start()

    bot_process = multiprocessing.Process(target=main_bot)
    bot_process.start()

    bot_process.join()
    uvicorn_process.join()
