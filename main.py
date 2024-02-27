import asyncio
from os import getenv
from json import loads

from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from src.kleen_skan import KleenSkanClient

load_dotenv()

bot = Bot(getenv("BOT_TOKEN"))
dp = Dispatcher()

kleen_scan_client = KleenSkanClient(loads(getenv("KLEEN_SKAN_TOKENS")))


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Send file to scan\nUse /change_token to change token")


@dp.message(Command(commands=["change_token"]))
async def change_token(message: types.Message):
    current_token_index = await kleen_scan_client.change_token()

    await message.answer(f"Token index changed to: `{current_token_index}`", parse_mode="Markdown")


@dp.message()
async def on_message(message: types.Message):
    if not message.document:
        await message.answer("Send file to scan")
        return

    file_info = await bot.get_file(message.document.file_id)
    binary_file = await bot.download_file(file_info.file_path)

    data = await kleen_scan_client.scan_file(binary_file)

    if data["httpResponseCode"] != 200:
        await message.answer(
            f"Error! Response status: {data['httpResponseCode']}\n`{data['message']}`\n\nTry /change\\_token",
            parse_mode="Markdown"
        )
        return

    if not data["success"]:
        await message.answer(data["error_message"])
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        types.InlineKeyboardButton(text="Check/update result", callback_data=data["data"]["scan_token"])
    )

    await message.answer(f"Scan token: `{data['data']['scan_token']}`", parse_mode="Markdown",
                         reply_markup=keyboard.as_markup())


@dp.callback_query()
async def update_result(callback: types.CallbackQuery):
    data = await kleen_scan_client.get_result(callback.data)

    if not data["success"]:
        await callback.message.answer(f"Error! Response status: {data['httpResponseCode']}\n`{data['message']}`",
                                      parse_mode="Markdown")
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        types.InlineKeyboardButton(text="Check/update result", callback_data=callback.data)
    )

    message_text = ""

    for scan in data["data"]:
        avname, flagname, status = scan["avname"], scan["flagname"], scan["status"]

        message_text += "✅" if flagname == "Undetected" else "⚠️" if status != "ok" else "⛔"
        message_text += f"{avname}: `{flagname}`\n"

    try:
        await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=keyboard.as_markup())
    except TelegramBadRequest:
        await callback.answer("Not updated")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
