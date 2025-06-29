import os
import asyncio
import logging
from aiogram import Bot, Dispatcher

from app.handlers import setup_handlers, setup_handlers2, setup_handlers3

from app.handlers import client




from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    )


async def main():
    global bot
    bot = Bot(token=os.getenv('TG_TOKEN'))
    # присваиваем глобальную переменную
    from app.config import bot as config_bot
    config_bot = bot



    dp = Dispatcher()
    setup_handlers(dp, bot)
    setup_handlers2(dp, bot)
    setup_handlers3(dp, bot)
    dp.include_router(client)
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)
    if bot is None:
        raise RuntimeError("Bot не был инициализирован!")
    await dp.start_polling(bot)


async def startup(dispatcher: Dispatcher):
    #await async_main()
    logging.info('Bot started up...')


async def shutdown(dispatcher: Dispatcher):
    logging.info('Bot is shutting down...')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Bot stopped')