# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 14/nov./2023  at 17:12 $'

import hashlib
from tkinter.filedialog import askopenfilename

import pandas as pd
import requests
import ttkbootstrap as ttk
from dotenv import dotenv_values
from static.extensions import secrets,  url_api
import templates.cb_functions as cb
from ttkbootstrap.tableview import Tableview


class FichajesFilesGUI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # -------------------create title-----------------
        self.df = None
        self.label_title = ttk.Label(self, text='Telintec Software Fichajes')
        self.label_title.grid(row=0, column=0, columnspan=3)
        # -------------------create entry for file selector-----------------
        self.label_file = ttk.Label(self, text='File: ')
        self.label_file.grid(row=1, column=0)
        self.file_entry = ttk.Button(self, text='Select File', command=self.button_file_click)
        self.file_entry.grid(row=1, column=1)
        self.label_filename = ttk.Label(self, text='')
        self.label_filename.grid(row=1, column=2)
        # -------------------create tableview for data-----------------
        self.table = Tableview(self)
        self.table.grid(row=2, column=0, columnspan=3)

    def button_file_click(self):
        try:
            filename = askopenfilename(filetypes=[('Excel Files', '*.xlsx'), ('Excel Files', '*.xls')])
            print("name: ", filename)
        except Exception as e:
            filename = e
        self.label_filename.configure(text=filename)
        self.file_entry.configure(text='File Selected')
        if ".xls" in filename or ".xlsx" in filename:
            # read excel
            skip_rows = [0, 1, 2]
            cols = [0, 1, 2]
            self.df = pd.read_excel('files/30_dias_ al_13-11-2023.xls', skiprows=skip_rows, usecols=cols)
            self.df.dropna(inplace=True)
            self.df["Fecha/hora"] = cb.clean_date(self.df["Fecha/hora"].tolist())
            self.df["Fecha/hora"] = pd.to_datetime(self.df["Fecha/hora"], format="mixed", dayfirst=True)
            self.df.dropna(subset=['Fecha/hora'], inplace=True)
            self.df["status"], self.df["name"], self.df["card"], self.df["in_out"] = cb.clean_text(self.df["Texto"].to_list())
            for i, col in enumerate(self.df.columns.tolist()):
                self.table.insert_column(i, col)
            self.table.insert_rows(0, self.df.values.tolist())
            self.table.update()


if __name__ == '__main__':
    app = ttk.Window()
    main = FichajesFilesGUI(app)
    main.pack()
    app.mainloop()
