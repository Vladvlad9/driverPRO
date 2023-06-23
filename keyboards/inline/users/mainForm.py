import requests
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.utils.callback_data import CallbackData
import datetime
import math

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import CONFIG
from crud import CRUDEvent
from schemas import EventSchema

main_cb = CallbackData("main", "target", "id", "editId")


class MainForms:

    @staticmethod
    async def main_ikb() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Погода", callback_data=main_cb.new("Weather", 0, 0)),
                    #InlineKeyboardButton(text="Мероприятия", callback_data=main_cb.new("Events", 0, 0))
                ]
            ]
        )

    @staticmethod
    async def back_ikb() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Назад", callback_data=main_cb.new("Main", 0, 0))
                ]
            ]
        )

    @staticmethod
    async def process(callback: CallbackQuery = None, message: Message = None, state: FSMContext = None) -> None:
        if callback:
            if callback.data.startswith("main"):
                data = main_cb.parse(callback_data=callback.data)

                if data.get("target") == "Main":
                    await callback.message.edit_text(text="Главное меню",
                                                     reply_markup=await MainForms.main_ikb())

                elif data.get("target") == "Weather":

                    response = requests.get(
                        f"https://api.openweathermap.org/data/2.5/weather?q=minsk&appid={CONFIG.APIWEATHER}&units=metric"
                    )
                    data = response.json()
                    cur_temp = data["main"]["temp"]
                    humidity = data["main"]["humidity"]
                    pressure = data["main"]["pressure"]
                    wind = data["wind"]["speed"]

                    sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
                    sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])

                    # продолжительность дня
                    length_of_the_day = datetime.datetime.fromtimestamp(
                        data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(data["sys"]["sunrise"])

                    code_to_smile = {
                        "Clear": "Ясно \U00002600",
                        "Clouds": "Облачно \U00002601",
                        "Rain": "Дождь \U00002614",
                        "Drizzle": "Дождь \U00002614",
                        "Thunderstorm": "Гроза \U000026A1",
                        "Snow": "Снег \U0001F328",
                        "Mist": "Туман \U0001F32B"
                    }

                    # получаем значение погоды
                    weather_description = data["weather"][0]["main"]

                    if weather_description in code_to_smile:
                        wd = code_to_smile[weather_description]
                    else:
                        # если эмодзи для погоды нет, выводим другое сообщение
                        wd = "Посмотри в окно, я не понимаю, что там за погода..."

                    await callback.message.edit_text(text=f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                                                          f"Погода в городе: Минск\n"
                                                          f"Температура: {cur_temp}°C <i>{wd}</i>\n"
                                                          f"Влажность: {humidity}%\n"
                                                          f"Давление: {math.ceil(pressure / 1.333)} мм.рт.ст\n"
                                                          f"Ветер: {wind} м/с \n"
                                                          f"Восход солнца: {sunrise_timestamp}\n"
                                                          f"Закат солнца: {sunset_timestamp}\n"
                                                          f"Продолжительность дня: {length_of_the_day}\n"
                                                          f"Хорошего дня!",
                                                     reply_markup=await MainForms.back_ikb(),
                                                     parse_mode="HTML"
                    )

                elif data.get("target") == "Events":
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
                            get_date = name.find('div', class_="ticket-box__info-row ticket-box__date").text.replace('\n', '').replace(' ', '')
                            get_place = name.find('div', class_="ticket-box__info-row ticket-box__place").text.replace('\n', '').lstrip().rstrip()

                            get_time = name.find('div', class_="ticket-box__info-row ticket-box__time").text.replace('\n', '').replace(' ', '')
                            data_name[get_name] = get_date, get_time, get_place, f"https://www.ticketpro.by{get_link}"
                        except Exception as e:
                            print(e)

                    data_list_events = []
                    data_list = ""

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

                    for i, j in data_name.items():
                        data_list += f'Название мероприятия - <i>{i}</i>\n' \
                                    f'Когда {j}\n\n'

                    await callback.message.edit_text(text=data_list,
                                                     reply_markup=await MainForms.back_ikb())

