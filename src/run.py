import asyncio
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app import db                #
from app.handlers import router

# Загрузка переменных окружения из .env
load_dotenv()

async def main():
    bot = Bot(token=os.getenv("TG_TOKEN"))
    dp = Dispatcher()
    # Подключаемся к БД (инициализируем connection pool)
    await db.connect()
    # Подключаем маршруты (router)
    dp.include_router(router)
    print("✅ Бот успешно запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())