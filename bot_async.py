"""
Бот синхронизации склада Бифит-кассы со складами маркетплэйсов.
"""
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from Clases.BifitApi.BifitSession import BifitSession
from methods import get_markets_products
from methods_async import *
from settings import YA_TOKEN, YA_CAMPAIGN_ID, YA_WHEREHOUSE_ID, ALI_TOKEN, VK_TOKEN, VK_OWNER_ID, VK_API_VER, \
    OZON_CLIENT_ID, OZON_ADMIN_KEY, USERNAME, PASSWORD, BOT_TOKEN

bifit_session = BifitSession(USERNAME, PASSWORD)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("tap /sync")


async def sync(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает процесс полной синхронизации всех маркетплэйсов со складом бифит-кассы"""

    bifit_tok = await bifit_session.token
    # bifit_tok = await get_bifit_token_async(USERNAME, PASSWORD)
    if bifit_tok is None:
        await update.message.reply_text(f"не получил токен бифит. сервер вернул ошибку."
                                        f" тапни /sync чтобы попробовать еще раз")
        return None
    await update.message.reply_text("получил токен бифит")

    my_org = await get_first_bifit_org_async(bifit_tok)
    if my_org is None:
        await update.message.reply_text(f"не получил список организаций. ошибка."
                                        f" тапни /sync чтобы попробовать еще раз")
        return None

    my_trade_obj = await get_first_bifit_trade_obj_async(bifit_tok, my_org.id)
    if my_trade_obj is None:
        await update.message.reply_text(f"не получил список торг объектов. ошибка."
                                        f" тапни /sync чтобы попробовать еще раз")
        return None

    await update.message.reply_text("получил данные по объекту и организации")
    goods_list = await get_bifit_products_list_async(bifit_tok, my_org.id, my_trade_obj.id)
    if goods_list is None:
        await update.message.reply_text(f"не получил список товаров. ошибка."
                                        f" тапни /sync чтобы попробовать еще раз")
        return None

    await update.message.reply_text("получил товары из бифит")

    ya_goods, ali_goods, vk_goods, ozon_goods = get_markets_products(goods_list)

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
    # on non command i.e message - echo the message on Telegram
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
