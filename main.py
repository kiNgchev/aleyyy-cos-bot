import asyncio
import csv
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = getenv("BOT_TOKEN")
ALEY_ID = getenv("ALEY_ID")
fieldnames = [
    "original_id", "copy_id"
]

dp = Dispatcher()


# TODO: Реализовать обработку выбора языка
async def handle_language_choosing(callback_query, lang: str):
    await callback_query.message.answer_photo(
        caption=,
        photo=BufferedInputFile.from_file('start_pic.png')
    )

@dp.callback_query(F.data == "lang_handler_ru")
async def handle_language_choosing_ru(callback_query):
    await handle_language_choosing(callback_query, 'ru')

@dp.callback_query(F.data == "lang_handler_en")
async def handle_language_choosing_en(callback_query):
    await handle_language_choosing(callback_query, 'en')


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard = [[
        InlineKeyboardButton(text="Russian", callback_data="lang_handler_ru"),
        InlineKeyboardButton(text="English", callback_data="lang_handler_en")
    ]])
    await message.answer(
        text="Choose your language:",
        reply_markup=keyboard
    )

@dp.message()
async def aley_handler(message: Message) -> None:
    if message.from_user.id != ALEY_ID:
        return

    if message.reply_to_message is None:
        return

    original_id = ''
    with open("pairs.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, fieldnames = fieldnames)
        for row in reader:
            if row["copy_id"] == message.reply_to_message.message_id:
                original_id = row['original_id']
        file.flush()

    try:
        await message.send_copy(chat_id=original_id)
    except TypeError:
        await message.answer("Что-то пошло не так.")


@dp.message()
async def members_handler(message: Message) -> None:
    if message.from_user.id == ALEY_ID:
        return
    try:
        send_message = await message.send_copy(chat_id=ALEY_ID)

        with open("pairs.csv", mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            row = {
                'original_id': message.message_id,
                'copy_id': send_message.message_id
            }

            writer.writerow(row)
            file.flush()

    except TypeError:
        await message.answer("Что-то пошло не так.")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())