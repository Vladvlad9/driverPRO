import asyncio
import math
import requests
from datetime import datetime
import pytz

from config import CONFIG
from loader import bot
from crud.userCRUD import CRUDUser


class WeatherBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.current_temperature = CONFIG.CURRENT_TEMPERATURE

    async def get_temperature_forecast(self):
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q=minsk&appid={self.api_key}&units=metric"
        )
        data = response.json()
        self.current_temperature = round(data["main"]["temp"])
        return self.current_temperature

    async def get_weather_description(self):
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q=minsk&appid={self.api_key}&units=metric"
        )
        data = response.json()
        weather_description = data["weather"][0]["main"]
        return weather_description

    async def get_weather_data(self):
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q=minsk&appid={self.api_key}&units=metric"
        )
        data = response.json()
        return data

    def format_weather_description(self, weather_description):
        code_to_smile = {
            "Clear": "Ясно \U00002600",
            "Clouds": "Облачно \U00002601",
            "Rain": "Дождь \U00002614",
            "Drizzle": "Дождь \U00002614",
            "Thunderstorm": "Гроза \U000026A1",
            "Snow": "Снег \U0001F328",
            "Mist": "Туман \U0001F32B"
        }

        if weather_description in code_to_smile:
            return code_to_smile[weather_description]
        else:
            return "Посмотри в окно, я не понимаю, что там за погода..."

    def format_temperature(self, temperature):
        return f"{temperature}°C"

    def format_pressure(self, pressure):
        return f"{math.ceil(pressure / 1.333)} мм.рт.ст"

    async def get_sunrise_time(self):
        data = await self.get_weather_data()
        sunrise_timestamp = datetime.fromtimestamp(data["sys"]["sunrise"])
        return sunrise_timestamp

    async def get_sunset_time(self):
        data = await self.get_weather_data()
        sunset_timestamp = datetime.fromtimestamp(data["sys"]["sunset"])
        return sunset_timestamp

    async def get_day_length(self):
        data = await self.get_weather_data()
        sunrise_timestamp = datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset_timestamp = datetime.fromtimestamp(data["sys"]["sunset"])
        length_of_the_day = sunset_timestamp - sunrise_timestamp
        return length_of_the_day

    async def send_weather_message(self):
        users = await CRUDUser.get_all()
        cur_temp = self.current_temperature
        weather_description = await self.get_weather_description()
        data = await self.get_weather_data()
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind = data["wind"]["speed"]
        sunrise_timestamp = await self.get_sunrise_time()
        sunset_timestamp = await self.get_sunset_time()
        length_of_the_day = await self.get_day_length()

        formatted_weather_description = self.format_weather_description(weather_description)
        formatted_temperature = self.format_temperature(cur_temp)
        formatted_pressure = self.format_pressure(pressure)

        current_time = datetime.now(pytz.timezone('Europe/Minsk')).strftime('%Y-%m-%d %H:%M')

        text = f"{current_time}\n" \
               f"Погода в городе: Минск\n" \
               f"Температура: {formatted_temperature} <i>{formatted_weather_description}</i>\n" \
               f"Влажность: {humidity}%\n" \
               f"Давление: {formatted_pressure}\n" \
               f"Ветер: {wind} м/с\n" \
               f"Восход солнца: {sunrise_timestamp}\n" \
               f"Закат солнца: {sunset_timestamp}\n" \
               f"Продолжительность дня: {length_of_the_day}\n" \
               f"Хорошего дня!"

        tasks = []
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

    async def send_temperature_change_message(self):
        users = await CRUDUser.get_all()
        cur_temp = self.current_temperature

        if await self.get_temperature_forecast() < cur_temp:
            text = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n" \
                   f"Погода немного ухудшилась\n" \
                   f"{round(cur_temp)}°C"

            tasks = []
            try:
                for user in users:
                    tasks.append(bot.send_message(chat_id=user.user_id,
                                                  text=text,
                                                  disable_web_page_preview=True)
                                 )

                await asyncio.gather(*tasks, return_exceptions=True)  # Отправка всем сразу
                CONFIG.CURRENT_TEMPERATURE = await self.get_temperature_forecast()
            except Exception as e:
                await bot.send_message(text=f"Ошибка при отправке конкретной температуре (temperature_change)\n {e}",
                                       chat_id=381252111)
        else:
            CONFIG.CURRENT_TEMPERATURE = await self.get_temperature_forecast()

    async def weather_description(self):
        text_description = ""
        users = await CRUDUser.get_all()

        get_weather_description = self.format_weather_description(await self.get_weather_description())
        if get_weather_description == "Rain" or get_weather_description == "Drizzle":
            text_description = "Скоро будет <i>Дождь</i>"
        elif get_weather_description == "Clouds":
            text_description = "Скоро будет <i>Облочно</i>"
        elif get_weather_description == "Thunderstorm":
            text_description = "Скоро будет <i>Гроза</i>"

        tasks = []
        try:
            for user in users:
                tasks.append(bot.send_message(chat_id=user.user_id,
                                              text=text_description,
                                              parse_mode="HTML",
                                              disable_web_page_preview=True)
                             )

            await asyncio.gather(*tasks, return_exceptions=True)  # Отправка всем сразу
            CONFIG.CURRENT_TEMPERATURE = await self.get_temperature_forecast()
        except Exception as e:
            await bot.send_message(text=f"Ошибка при отправке (weather_description)\n {e}",
                                   chat_id=381252111)

