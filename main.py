# Точка входа, код запуска бота и инициализации всех остальных модулей

import asyncio  # Для асинхронного запуска бота
import logging  # Для настройки логирования, которое поможет в отладке

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode  # Настройки разметки сообщений
from aiogram.fsm.storage.memory import MemoryStorage  # Хранилища данных для состояний пользователей

from config import _BOT_TOKEN  # Настройки бота
from handlers import router
from kb import set_main_menu


async def main():  # В этой функции будет запускаться бот

    # Создаём объект бота с нашим токеном
    bot = Bot(token=_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Параметр parse_mode отвечает за используемую по умолчанию разметку сообщений
    # Используем HTML, чтобы избежать проблем с экранированием символов
    dp = Dispatcher(storage=MemoryStorage())  # Создаём объект диспетчера
    # Параметр говорит о том, что все данные бота, которые мы не сохраняем в БД, будут стерты при перезапуске
    dp.include_router(router)  # Подключает к нашему диспетчеру все обработчики, которые используют router
    await set_main_menu(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    # Удаляет все обновления, которые произошли после последнего завершения работы бота
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())  # Запускает бота


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
