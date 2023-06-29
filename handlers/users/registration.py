import requests
from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from aiogram.utils.exceptions import BadRequest
from bs4 import BeautifulSoup

from crud import CRUDEvent
from crud.userCRUD import CRUDUser
from keyboards.inline.users.mainForm import main_cb, MainForms
from loader import dp, bot
from schemas import UserSchema, EventSchema
from states.users.userState import UserStates


@dp.message_handler(commands=["start"])
async def registration_start(message: types.Message):
    user = await CRUDUser.get(user_id=message.from_user.id)
    if not user:
        await CRUDUser.add(user=UserSchema(user_id=message.from_user.id))
    await message.answer(text='Главное меню', reply_markup=await MainForms.main_ikb())


@dp.callback_query_handler(main_cb.filter())
@dp.callback_query_handler(main_cb.filter(), state=UserStates.all_states)
async def process_callback(callback: types.CallbackQuery, state: FSMContext = None):
    await MainForms.process(callback=callback, state=state)


@dp.message_handler(state=UserStates.all_states, content_types=["text"])
async def process_message(message: types.Message, state: FSMContext):
    await MainForms.process(message=message, state=state)

