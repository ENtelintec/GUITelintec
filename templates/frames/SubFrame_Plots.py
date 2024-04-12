# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 18/ene./2024  at 15:48 $'

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import tkinter as tk
import matplotlib

matplotlib.use('TkAgg')
width_bar = 0.1


class FramePlot(tk.Frame):
    def __init__(self, master, data=None, type_chart=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        if data is not None:
            match type_chart:
                case 'bar':
                    labels_x = data["data"].keys()
                    values = data["data"].values()
                    figure = Figure(figsize=(6, 4), dpi=100)
                    figure_canvas = FigureCanvasTkAgg(figure, self)
                    NavigationToolbar2Tk(figure_canvas, self)
                    axes = figure.add_subplot()
                    if isinstance(list(values)[0], list):
                        values = np.array(list(values))
                        values = values.T
                        indexes = np.arange(len(labels_x))
                        for index_k, values_k in enumerate(values):
                            axes.bar(indexes + index_k * width_bar, values_k, width=width_bar)
                        axes.set_xticks(indexes)
                        axes.set_xticklabels(labels_x)
                    else:
                        axes.bar(labels_x, values)
                    axes.set_title(data["title"])
                    axes.set_ylabel(data["ylabel"])
                    figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)
                case 'scatter':
                    x_values = data["val_x"]
                    y_values = data["val_y"]
                    figure = Figure(figsize=(6, 4), dpi=100)
                    figure_canvas = FigureCanvasTkAgg(figure, self)
                    NavigationToolbar2Tk(figure_canvas, self)
                    axes = figure.add_subplot()
                    axes.scatter(x_values, y_values)
                    axes.set_title('Scatter Plot')
                    axes.set_xlabel('X Values')
                    axes.set_ylabel('Y Values')
                    figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)
                case 'histogram':
                    n_bins = data["n_bins"]
                    values = data["values"]
                    figure = Figure(figsize=(6, 4), dpi=100)
                    figure_canvas = FigureCanvasTkAgg(figure, self)
                    NavigationToolbar2Tk(figure_canvas, self)
                    axes = figure.add_subplot()
                    axes.hist(values, n_bins)
                    axes.set_title('Histogram')
                    axes.set_xlabel('Values')
                    axes.set_ylabel('Frequency')
                    figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)
                case 'boxplot':
                    data_box = data["data"]
                    labels = data["labels"]
                    figure = Figure(figsize=(6, 4), dpi=100)
                    figure_canvas = FigureCanvasTkAgg(figure, self)
                    NavigationToolbar2Tk(figure_canvas, self)
                    axes = figure.add_subplot()
                    axes.boxplot(data_box, labels=labels)
                    axes.set_title('Box Plot')
                    axes.set_ylabel('Values')
                    figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)
                case _:
                    x_values = data["val_x"]
                    y_values = data["val_y"]
                    figure = Figure(figsize=(6, 4), dpi=100)
                    figure_canvas = FigureCanvasTkAgg(figure, self)
                    NavigationToolbar2Tk(figure_canvas, self)
                    axes = figure.add_subplot()
                    if isinstance(y_values[0], list):
                        values = np.array(y_values)
                        values = values.T
                        indexes = np.arange(len(x_values))
                        for index_k, values_k in enumerate(values):
                            axes.plot(indexes, values_k)
                        axes.set_xticks(indexes)
                        axes.set_xticklabels(x_values)
                    else:
                        axes.plot(x_values, y_values)
                    axes.set_title(data["title"])
                    axes.set_xlabel('X Values')
                    axes.set_ylabel('Y Values')
                    figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)
