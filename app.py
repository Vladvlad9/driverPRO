import asyncio
from datetime import datetime
from aiogram import Bot
import requests
from bs4 import BeautifulSoup

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
                                              text="text_event",
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

        await asyncio.gather(*tasks, return_exceptions=True)  # Отправка всем админам сразу
    except Exception as e:
        await bot.send_message(text=f"Ошибка при отправке количестве мероприятий\n {e}",
                               chat_id=381252111)


    # await bot.send_message(chat_id=381252111, text=f"Сегодня {current_date} в Минске пройдет "
    #                                                f"{len(current_date_event)} мероприятий\n\n"
    #                                                f"{text_event}",
    #                        disable_web_page_preview=True)


async def min_max_time(event: list):
    time_list = []

    for i in event:
        time_list.append(i.time_event)

    # Преобразование строковых значений времени в объекты datetime
    time_objects = [datetime.strptime(time_str, '%H:%M') for time_str in time_list]

    # Поиск минимального и максимального времени
    min_time = min(time_objects)
    max_time = max(time_objects)

    data_list_time = [min_time.strftime('%H:%M'), max_time.strftime('%H:%M')]
    return data_list_time


async def on_startup(_):
    # time_format = '%H:%M'
    #
    # start_time = datetime.strptime('19:00', time_format)
    # end_time = datetime.strptime('11:00', time_format)
    #
    # # Если начальное время находится после конечного времени, добавьте один день к конечному времени
    # if start_time < end_time:
    #     end_time = end_time.replace(day=end_time.day + 1)
    #
    # time_difference = start_time - end_time
    # seconds_difference = time_difference.total_seconds()
    #
    # print('Разница в секундах:', seconds_difference)
    await set_default_commands(dp)
    current_date = datetime.now().strftime("%d.%m.%Y")
    events = list(filter(lambda x: x.date_event == current_date, await CRUDEvent.get_all()))
    if events:
        get_time = await min_max_time(event=events)

        scheduler = AsyncIOScheduler()

        scheduler.add_job(get_def_scheduler,
                          trigger=CronTrigger(hour='17', minute='13'),
                          kwargs={'bot': bot})
        #scheduler.add_job(get_def_scheduler, trigger='cron', hour='10-21', minute='*/1', second='30', kwargs={'bot': bot})

        first_event_time = get_time[0][:-3]
        last_event_time = get_time[1][:-3]

        scheduler.add_job(func=eventsOfDay,
                          trigger=CronTrigger(
                              hour=f'{int(first_event_time)}-{int(last_event_time) + 1}',
                              minute=0),
                          kwargs={'bot': bot})
        scheduler.start()

    # #scheduler.add_job(event_verification, trigger='date', run_date=datetime.now() + timedelta(seconds=10))
    # for i in events:
    #     scheduler.add_job(test,
    #                       trigger='cron',
    #                       hour=int(i.time_event[:-3]),
    #                       minute=int(i.time_event[3:]),
    #                       start_date=datetime.now(),
    #                       kwargs={'a': i.name}
    #                       )


if __name__ == '__main__':
    from aiogram import executor, types
    from handlers import dp

    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
