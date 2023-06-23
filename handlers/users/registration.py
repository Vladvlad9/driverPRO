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


@dp.message_handler(commands=["getevent"])
async def registration_start(message: types.Message):
    res = requests.get(
        "https://www.ticketpro.by/"
    )
    data_name = {}

    soup = BeautifulSoup(res.text, 'html.parser')

    names = soup.findAll('div', class_='ticket-box__body')

    for name in names:
        try:
            get_name = name.find('div', class_="ticket-box__title").text.replace('\n', '')
            get_link = name.find('a', class_='btn btn-default').get('href')
            get_date = name.find('div', class_="ticket-box__info-row ticket-box__date").text.replace('\n', '').replace(
                ' ', '')
            get_place = name.find('div', class_="ticket-box__info-row ticket-box__place").text.replace('\n',
                                                                                                       '').lstrip().rstrip()

            get_time = name.find('div', class_="ticket-box__info-row ticket-box__time").text.replace('\n', '').replace(
                ' ', '')
            data_name[get_name] = get_date, get_time, get_place, f"https://www.ticketpro.by{get_link}"
        except Exception:
            pass

    data_list_events = []

    events = await CRUDEvent.get_all()
    for i in events:
        data_list_events.append(i.name)

    for name, data_event in data_name.items():
        if name not in data_list_events:
            await CRUDEvent.add(event=EventSchema(name=name,
                                                  date_event=data_event[0],
                                                  time_event=data_event[1],
                                                  place=data_event[2],
                                                  link=data_event[3])
                                )


@dp.callback_query_handler(main_cb.filter())
@dp.callback_query_handler(main_cb.filter(), state=UserStates.all_states)
async def process_callback(callback: types.CallbackQuery, state: FSMContext = None):
    await MainForms.process(callback=callback, state=state)


@dp.message_handler(state=UserStates.all_states, content_types=["text"])
async def process_message(message: types.Message, state: FSMContext):
    await MainForms.process(message=message, state=state)

