# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 18/ene./2024  at 15:48 $'

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import tkinter as tk
import matplotlib

matplotlib.use('TkAgg')


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
                    axes.plot(x_values, y_values)
                    axes.set_title('Plot')
                    axes.set_xlabel('X Values')
                    axes.set_ylabel('Y Values')
                    figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=10, pady=10)


if __name__ == '__main__':
    window = tk.Tk()
    window.title('Matplotlib Demo')
    window.columnconfigure(0, weight=1)
    label = tk.Label(window, text='Matplotlib Demo')
    label.grid(row=0, column=0)
    data_plot = {"data": {'Python': 11.27, 'C': 11.16, 'Java': 10.46, 'C++': 7.5, 'C#': 5.26},
                 "title": "Language Popularity",
                 "ylabel": "Popularity"
                 }
    app = FramePlot(window, data_plot, type_chart='bar', width=300)
    app.grid(row=1, column=0)
    label2 = tk.Label(window, text='Matplotlib Demo label 2')
    label2.grid(row=2, column=0)
    app.mainloop()
    print("Hecho por Edisson Naula, 2023-1-18, version 1.0")
