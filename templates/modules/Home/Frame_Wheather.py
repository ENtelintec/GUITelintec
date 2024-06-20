# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 16:14 $'

import ttkbootstrap as ttk
import python_weather
import asyncio

from templates.Functions_Utils import create_label

days_of_week = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}


class WeatherFrame(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure((0, 1), weight=1)
        self.weather = None
        self.daily_forecasts = None
        self.hourly_forecasts = None
        self.city = "Monterrey"
        frame_weather = ttk.Frame(self)
        frame_weather.grid(row=1, column=0, sticky="nsew")
        asyncio.run(self.create_widgets(frame_weather))

    async def getweather(self):
        # declare the client. the measuring unit used defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(unit=python_weather.METRIC) as client:
            # fetch a weather forecast from a city
            self.weather = await client.get(self.city)           
            # get the weather forecast for a few days
            self.hourly_forecasts = []
            self.daily_forecasts = []
            for daily in self.weather.daily_forecasts:
                self.daily_forecasts.append(daily)
                # hourly forecasts
                for hourly in daily.hourly_forecasts:
                    self.hourly_forecasts.append(hourly)

    async def create_widgets(self, master):
        await self.getweather()
        # -----------------------Title-----------------
        master.columnconfigure(0, weight=1)
        create_label(master, 0, 0, text=f"Clima en: {self.weather.location}", font=("Helvetica", 14, "bold"), columnspan=2)
        frame_current = ttk.Frame(master)
        frame_current.grid(row=1, column=0, sticky="nsew")
        # -----------------------Frames---------------------------
        create_label(frame_current, 0, 0, text=f"{self.weather.temperature} ºC", font=("Helvetica", 30, "bold"),  rowspan=4)
        create_label(frame_current, 0, 1, text=f"Humedad: {self.weather.humidity}%", font=("Helvetica", 8, "normal"))
        create_label(frame_current, 1, 1, text=f"Viento: {self.weather.wind_direction} {self.weather.wind_speed} km/h", font=("Helvetica", 8, "normal"))
        create_label(frame_current, 2, 1, text=f"{self.weather.description}", font=("Helvetica", 8, "normal"))
        create_label(frame_current, 3, 1, text=f"Sensación: {self.weather.feels_like} ºC", font=("Helvetica", 8, "normal"))
        frame_daily = ttk.Frame(self)
        frame_daily.grid(row=1, column=1, sticky="we")
        indexes = []
        for day, daily in enumerate(self.daily_forecasts):
            create_label(frame_daily, 0, day, text=f"{days_of_week[daily.date.weekday()]}: ", font=("Helvetica", 10, "bold"))
            create_label(frame_daily, 1, day, text=f"{daily.highest_temperature} ºC", font=("Helvetica", 10, "bold"))
            create_label(frame_daily, 2, day, text=f"{daily.lowest_temperature} ºC", font=("Helvetica", 10, "bold"))
            indexes.append(day)
        frame_daily.columnconfigure(indexes, weight=1)
