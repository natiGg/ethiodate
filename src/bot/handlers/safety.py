from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="safety")

@router.message(Command("report"))
async def cmd_report(message: Message):
    await message.answer("Please provide details about the profile you are reporting.")

@router.message(Command("block"))
async def cmd_block(message: Message):
    await message.answer("User blocked.")
