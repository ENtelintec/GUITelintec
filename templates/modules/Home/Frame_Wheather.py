# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 16:14 $'

import ttkbootstrap as ttk
import python_weather
import asyncio

from templates.Funtions_Utils import create_label

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
        create_label(self, 0, 0, text=f"Clima en: {self.weather.location}", font=("Helvetica", 14, "bold"), columnspan=2)
        # -----------------------Frames---------------------------
        create_label(master, 1, 0, text="Hoy: ", font=("Helvetica", 10, "bold"))
        create_label(master, 1, 1, text=f"{self.weather.temperature} ", font=("Helvetica", 10, "bold"))
        indexes = []
        for day, daily in enumerate(self.daily_forecasts):
            create_label(master, 2, day*2, text=f"{days_of_week[daily.date.weekday()]}: ", font=("Helvetica", 10, "bold"))
            create_label(master, 2, day*2 + 1, text=f"{daily.temperature} ", font=("Helvetica", 10, "bold"))
            indexes.append(day)
        master.columnconfigure(indexes, weight=1)
