import asyncio
import math
from datetime import datetime
from aiogram import Bot
import requests
from bs4 import BeautifulSoup

from config import CONFIG
from crud import CRUDEvent
from crud.userCRUD import CRUDUser
from loader import bot
from schemas import EventSchema
from utils.set_bot_commands import set_default_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


async def event_verification():  # сдлеать раз в сутки например в 6 утра, что бы проверяло есть ли новые мероприятия
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


async def eventsOfDay(bot: Bot):
    current_date = datetime.now().strftime("%d.%m.%Y")
    now_hour = datetime.now().strftime("%H:%M")
    text_event = ''
    events = list(filter(lambda x: x.date_event == current_date, await CRUDEvent.get_all()))
    count = 1

    users = await CRUDUser.get_all()
    tasks = []

    for event in events:
        if event.time_event == now_hour:
            text_event += f"Началось мероприятие №{count}:\n" \
                          f"Название: {event.name}\n" \
                          f"Место: {event.place}\n" \
                          f"Время начала {event.time_event}\n" \
                          f'<a href="{event.link}">Ссылка</a>\n\n'
        count += 1

    if not text_event == '':
        #await bot.send_message(chat_id=381252111, text=text_event, disable_web_page_preview=True)
        try:
            for user in users:
                tasks.append(bot.send_message(chat_id=user.user_id,
                                              text=text_event,
                                              disable_web_page_preview=True)
                             )

            await asyncio.gather(*tasks, return_exceptions=True)  # Отправка всем админам сразу
        except Exception as e:
            await bot.send_message(text=f"Ошибка при отправке конкретного мероприятия\n {e}",
                                   chat_id=381252111)


async def get_def_scheduler(bot: Bot):
    users = await CRUDUser.get_all()
    tasks = []

    current_date = datetime.now().strftime("%d.%m.%Y")
    current_date_event = list(filter(lambda x: x.date_event == current_date, await CRUDEvent.get_all()))
    text_event = ""
    count = 1

    for current_event in current_date_event:
        text_event += f"№{count}:\n" \
                      f"Название: {current_event.name}\n" \
                      f"Место: {current_event.place}\n" \
                      f"Время начала {current_event.time_event}\n" \
                      f'<a href="{current_event.link}">Ссылка</a>\n\n'
        count += 1

    try:
        for user in users:
            tasks.append(bot.send_message(chat_id=user.user_id,
                                          text=f"Сегодня {current_date} в Минске пройдет "
                                               f"{len(current_date_event)} мероприятий\n\n"
                                               f"{text_event}",
                                          disable_web_page_preview=True)
                         )

        await asyncio.gather(*tasks, return_exceptions=True)  # Отправка всем сразу
    except Exception as e:
        await bot.send_message(text=f"Ошибка при отправке количестве мероприятий\n {e}",
                               chat_id=381252111)


async def sorted_time(event: list):
    time_list = []

    for i in event:
        time_list.append(i.time_event)

    sorted_time_list = sorted(time_list, key=lambda x: datetime.strptime(x, '%H:%M'))

    return sorted_time_list


async def get_temperature_forecast():
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q=minsk&appid={CONFIG.APIWEATHER}&units=metric"
    )
    data = response.json()
    cur_temp = data["main"]["temp"]
    return cur_temp


async def weather(bot: Bot):
    users = await CRUDUser.get_all()
    tasks = []

    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q=minsk&appid={CONFIG.APIWEATHER}&units=metric"
    )
    data = response.json()
    cur_temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind = data["wind"]["speed"]

    sunrise_timestamp = datetime.fromtimestamp(data["sys"]["sunrise"])
    sunset_timestamp = datetime.fromtimestamp(data["sys"]["sunset"])

    # продолжительность дня
    length_of_the_day = datetime.fromtimestamp(
        data["sys"]["sunset"]) - datetime.fromtimestamp(data["sys"]["sunrise"])

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

    text = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"\
           f"Погода в городе: Минск\n"\
           f"Температура: {cur_temp}°C <i>{wd}</i>\n"\
           f"Влажность: {humidity}%\n"\
           f"Давление: {math.ceil(pressure / 1.333)} мм.рт.ст\n"\
           f"Ветер: {wind} м/с \n"\
           f"Восход солнца: {sunrise_timestamp}\n"\
           f"Закат солнца: {sunset_timestamp}\n"\
           f"Продолжительность дня: {length_of_the_day}\n"\
           f"Хорошего дня!"
    CONFIG.CURRENT_TEMPERATURE = cur_temp
    try:
        for user in users:
            tasks.append(bot.send_message(chat_id=user.user_id,
                                          text=text,
                                          parse_mode="HTML",
                                          disable_web_page_preview=True)
                         )

        await asyncio.gather(*tasks, return_exceptions=True)  # Отправка всем сразу
    except Exception as e:
        await bot.send_message(text=f"Ошибка при отправке количестве мероприятий\n {e}",
                               chat_id=381252111)


async def temperature_change(bot: Bot):
    users = await CRUDUser.get_all()
    tasks = []

    text = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n" \
           f"Погода немного ухудшилась\n" \
           f"{CONFIG.CURRENT_TEMPERATURE}°C"

    try:
        for user in users:
            tasks.append(bot.send_message(chat_id=user.user_id,
                                          text=text,
                                          disable_web_page_preview=True)
                         )

        await asyncio.gather(*tasks, return_exceptions=True)  # Отправка всем сразу
    except Exception as e:
        await bot.send_message(text=f"Ошибка при отправке конкретной температуре (temperature_change)\n {e}",
                               chat_id=381252111)


async def on_startup(_):
    await set_default_commands(dp)
    current_date = datetime.now().strftime("%d.%m.%Y")
    events = list(filter(lambda x: x.date_event == current_date, await CRUDEvent.get_all()))

    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

    scheduler.add_job(event_verification,
                      trigger=CronTrigger(hour=5, minute=30))  # Функция которая будет проверять новые мероприятия

    get_temperature = await get_temperature_forecast()

    if get_temperature < CONFIG.CURRENT_TEMPERATURE:
        CONFIG.CURRENT_TEMPERATURE = get_temperature

        scheduler.add_job(temperature_change,
                          trigger=CronTrigger(hour="8-22", minute="*/55"),
                          kwargs={'bot': bot})  # Функция которая будет проверять сколько мероприятий проходит сегодня

    if events:
        get_time = await sorted_time(event=events)

        scheduler.add_job(get_def_scheduler,
                          trigger=CronTrigger(hour=7, minute=0),
                          kwargs={'bot': bot})  # Функция которая будет проверять сколько мероприятий проходит сегодня

        scheduler.add_job(weather,
                          trigger=CronTrigger(hour=7, minute=1),
                          kwargs={'bot': bot})  # Функция отправки погоды

        for h in get_time:
            get_hour = int(h[:-3])
            get_minute = int(h[3:])

            scheduler.add_job(func=eventsOfDay,
                              trigger=CronTrigger(hour=get_hour, minute=get_minute),
                              kwargs={'bot': bot})

        scheduler.start()


if __name__ == '__main__':
    from aiogram import executor, types
    from handlers import dp

    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
