import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand
import os

# Получаем токен из переменных окружения Railway
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise Exception("ERROR: TOKEN is not set! Add your Telegram bot token in Railway Environment Variables.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Структура: tasks[chat_id][user_id] = список задач
tasks = {}

@dp.message(Command("repeat"))
async def repeat_text(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Команда работает только в группе.")
        return

    try:
        # /repeat <кол-во> <интервал_мин> <текст>
        parts = message.text.split(maxsplit=3)
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
                    await message.answer(text)
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(send_repeated())

        chat_tasks = tasks.setdefault(message.chat.id, {})
        user_tasks = chat_tasks.setdefault(message.from_user.id, [])
        user_tasks.append(task)

    except (IndexError, ValueError):
        await message.answer(
            "Использование:\n/repeat <кол-во> <интервал_мин> <текст>"
        )

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

async def main():
    await bot.set_my_commands([
        BotCommand(command="repeat", description="Повторить сообщение"),
        BotCommand(command="stop", description="Остановить свои повторения")
    ])
    # polling удобно для бесплатных Railway проектов
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())