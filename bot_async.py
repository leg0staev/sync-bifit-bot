"""
Бот синхронизации склада Бифит-кассы со складами маркетплэйсов.
"""
import asyncio

# from logger import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from Clases.BifitApi.BifitSession import BifitSession
from methods import get_markets_products, parse_calculation, get_write_off_msg, products_write_off, \
    goods_list_to_csv_str
from methods_async import *
from settings import YA_TOKEN, YA_CAMPAIGN_ID, YA_WHEREHOUSE_ID, ALI_TOKEN, VK_TOKEN, VK_OWNER_ID, VK_API_VER, \
    OZON_CLIENT_ID, OZON_ADMIN_KEY, USERNAME, PASSWORD, BOT_TOKEN

bifit_session = BifitSession(USERNAME, PASSWORD)


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
    goods_set = await bifit_session.get_bifit_products_set_async()
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

    goods_set = await bifit_session.get_bifit_products_set_async()

    if goods_set is None:
        await update.message.reply_text(f"не получил список товаров от Бифит. ошибка."
                                        f" тапни /sync чтобы попробовать еще раз")
        return None

    await update.message.reply_text("получил товары из бифит")

    ya_goods, ali_goods, vk_goods, ozon_goods = get_markets_products(goods_set)

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


def main() -> None:
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
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
