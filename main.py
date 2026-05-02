import asyncio
import csv
import logging
import sys
from contextlib import suppress
from os import getenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from aiogram_i18n import I18nMiddleware, I18nContext
from aiogram_i18n.cores import FluentRuntimeCore

TOKEN = getenv("TOKEN")
ALEY_ID = int(getenv("ALEY_ID"))
fieldnames = ["original_chat_id", "original_message_id", "copy_id"]

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="English", callback_data="en")],
            [InlineKeyboardButton(text="Русский", callback_data="ru")]
        ]
    )
    await message.answer("Choose language:", reply_markup=keyboard)


@router.callback_query(F.data == "en")
async def handle_en_switch(callback: CallbackQuery, i18n: I18nContext):
    await handle_lang_switch(callback, i18n, "en")


@router.callback_query(F.data == "ru")
async def handle_en_switch(callback: CallbackQuery, i18n: I18nContext):
    await handle_lang_switch(callback, i18n, "ru")


async def handle_lang_switch(callback: CallbackQuery, i18n: I18nContext, locale_code: str):
    await i18n.set_locale(locale_code)
    await callback.message.delete()
    await callback.message.answer_photo(
        caption=i18n.get('Start'),
        photo=FSInputFile('./img/start_pic.jpg'),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=i18n.get('Memo'), url='https://t.me/aleyyycosplay/1327')]
            ]
        )
    )


async def aley_handler(message: Message) -> None:
    if message.reply_to_message is None:
        return

    original_chat_id = None
    original_message_id = None

    with open("pairs.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, fieldnames = fieldnames)
        for row in reader:
            if row["copy_id"] == str(message.reply_to_message.message_id):
                original_chat_id = int(row['original_chat_id'])
                original_message_id = int(row['original_message_id'])
        file.flush()

    if original_chat_id is None or original_message_id is None:
        return

    try:
        await message.send_copy(chat_id=original_chat_id, reply_to_message_id=original_message_id)
    except TypeError:
        await message.answer("Somthing went wrong")


async def members_handler(message: Message, i18n: I18nContext) -> None:
    try:
        send_message = await message.send_copy(chat_id=ALEY_ID)

        with open("pairs.csv", mode="a+", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            row = {
                'original_chat_id': message.chat.id,
                'original_message_id': message.message_id,
                'copy_id': send_message.message_id
            }

            writer.writerow(row)
            file.flush()
        await message.answer(i18n.get('Success'))
    except TypeError:
        await message.answer("Somthing went wrong")


@router.message()
async def message_handler(message: Message, i18n: I18nContext) -> None:
    if message.from_user.id == ALEY_ID:
        await aley_handler(message)
    else:
        await members_handler(message, i18n)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp = Dispatcher()
    dp.include_router(router)

    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(
            path="locales/{locale}/LC_MESSAGES"
        ),
        default_locale='ru'
    )
    i18n_middleware.setup(dispatcher=dp)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())