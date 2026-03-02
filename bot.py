import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand
import os

# Получаем токен из переменных окружения Railway
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise Exception("ERROR: TOKEN is not set! Добавьте ваш токен от BotFather в Environment Variables.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Структура для хранения задач: tasks[chat_id][user_id] = список задач
tasks = {}

# Команда /repeat
@dp.message(Command("repeat"))
async def repeat_text(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Команда работает только в группе.")
        return

    try:
        # Проверяем, что есть все параметры
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            await message.answer("Использование:\n/repeat <кол-во> <интервал_мин> <текст>")
            return

        count = int(parts[1])
        minutes = int(parts[2])
        text = parts[3]
        interval = minutes * 60

        # Первое сообщение сразу
        await message.answer(f"✅ Первое сообщение: {text}")

        async def send_repeated():
            try:
                for _ in range(count - 1):  # первый раз уже отправили
                    await asyncio.sleep(interval)
                    try:
                        await message.answer(text)
                    except Exception as e:
                        logging.error(f"Ошибка при отправке сообщения: {e}")
            except asyncio.CancelledError:
                logging.info(f"Задача пользователя {message.from_user.id} отменена")

        # Создаём задачу
        task = asyncio.create_task(send_repeated())

        # Сохраняем задачу для пользователя
        chat_tasks = tasks.setdefault(message.chat.id, {})
        user_tasks = chat_tasks.setdefault(message.from_user.id, [])
        user_tasks.append(task)

    except ValueError:
        await message.answer("Ошибка: кол-во и интервал должны быть числами.")

# Команда /stop
@dp.message(Command("stop"))
async def stop_repeat(message: types.Message):
    chat_tasks = tasks.get(message.chat.id, {})
    user_tasks = chat_tasks.get(message.from_user.id, [])

    if user_tasks:
        for task in user_tasks:
            task.cancel()
        chat_tasks.pop(message.from_user.id)
        await message.answer("⛔ Ваши повторения остановлены.")
    else:
        await message.answer("У вас нет активных повторений.")

# Устанавливаем команды в Telegram
async def set_commands():
    await bot.set_my_commands([
        BotCommand(command="repeat", description="Повторить сообщение"),
        BotCommand(command="stop", description="Остановить свои повторения")
    ])

# Главная функция
async def main():
    await set_commands()
    await dp.start_polling(bot)  # Polling проще для Railway Free

if __name__ == "__main__":
    asyncio.run(main())
    # Для Railway Free лучше использовать polling, так как webhook может быть сложнее настроить.