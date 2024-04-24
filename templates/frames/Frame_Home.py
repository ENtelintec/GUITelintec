# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 23/abr./2024  at 15:34 $'

import asyncio

import python_weather
from python_weather.forecast import Forecast, DailyForecast, HourlyForecast
import ttkbootstrap as ttk

from templates.Funtions_Utils import create_label
from templates.frames.Frame_EmployeeDetail import EmployeeDetails
from templates.frames.SubFrame_SMDashboard import SMDashboard
from templates.screens.Home import HomeScreen

avaliable_dashboards = {
    # "sm": SMDashboard,
    "almacen": HomeScreen,
    # "rrhh": EmployeeDetails,
}


class HomeFrame(ttk.Frame):
    def __init__(self, master=None, data=None, data_emp=None, *args, **kwargs):
        super().__init__(master)
        self.master = master
        self.data = data if data is not None else None
        self.data_emp = data_emp if data_emp is not None else None
        # -----------------Title-------------------------------
        create_label(self, 0, 0, text="Home", font=("Helvetica", 30, "bold"), columnspan=2)
        frame_wather = WeatherFrame(self)
        frame_wather.grid(row=1, column=0, sticky="nsew")
        for index, dashboard in enumerate(avaliable_dashboards.keys()):
            frame = avaliable_dashboards[dashboard](self, **kwargs)
            frame.grid(row=2+index, column=0, sticky="nsew")


class WeatherFrame(ttk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master)
        self.weather = None
        self.daily_forecasts = None
        self.hourly_forecasts = None
        self.city = "Monterrey"
        asyncio.run(self.create_widgets(self))

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
        create_label(self, 0, 0, text=f"Clima {self.weather.location}", font=("Helvetica", 22, "bold"), columnspan=2)
        # -----------------------Frames---------------------------
        create_label(self, 1, 0, text=f"Temperatura", font=("Helvetica", 14, "bold"))
        create_label(self, 1, 1, text=f"{self.weather.temperature} ", font=("Helvetica", 14, "bold"))
        for day, daily in enumerate(self.daily_forecasts):
            create_label(self, 2, 0 + day, text=f"{daily.date}", font=("Helvetica", 14, "bold"))
            create_label(self, 3, 0 + day, text=f"{daily.temperature} ", font=("Helvetica", 14, "bold"))

