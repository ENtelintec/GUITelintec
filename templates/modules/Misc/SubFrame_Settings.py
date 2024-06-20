# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 15/may./2024  at 10:46 $'

import os
from datetime import datetime
from tkinter import filedialog

import pandas as pd
import ttkbootstrap as ttk

from static.extensions import filepath_settings
from templates.Functions_Files import update_file_settings, open_file_settings
from templates.Functions_Utils import create_button, create_label, select_path, set_dateEntry_new_value, create_Combobox
from templates.controllers.index import DataHandler


def save_settings_fun(department: str, config: dict):
    flag, settings = open_file_settings(filepath_settings)
    if not flag:
        return
    settings["gui"][department] = config
    update_file_settings(filepath_settings, settings)


class SettingsSM(ttk.Frame):
    def __init__(self, master, settings, department, style_gui, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure(0, weight=1)
        # -----------------------title--------------------------------------
        create_label(self, 0, 0, text="Configuraciones SM",
                     font=("Arial", 18, "bold"))


class SettingsRRHH(ttk.Frame):
    def __init__(self, master, settings, department, style_gui, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.columnconfigure(1, weight=1)
        self.settings = settings
        self.department = department
        self.style_gui = style_gui
        files_procces, files_cache = self._get_data_from_settings()
        # Title label
        create_label(self, 0, 0, text="Configuraciones R.R.H.H.",
                     font=("Arial", 18, "bold"))
        # -------------------------path carpeta archivos------------------------
        create_label(self, 1, 0, text="Ruta de archivos: ",
                     font=("Arial", 14, "normal"))
        self.entry_path_files = ttk.StringVar()
        self.entry_path_files.set(files_procces)
        ttk.Entry(self, textvariable=self.entry_path_files).grid(
            row=1, column=1, sticky="nswe")
        # boton para seleccionar carpeta
        create_button(self, 2, 0, text="Seleccionar",
                      command=self._select_path_file,
                      width=10, sticky="n")
        # ------------------------path carpeta cache----------------------------
        create_label(self, 3, 0, text="Ruta de cache: ",
                     font=("Arial", 14, "normal"))
        self.entry_path_cache = ttk.StringVar()
        self.entry_path_cache.set(files_cache)
        ttk.Entry(self, textvariable=self.entry_path_cache).grid(
            row=3, column=1, sticky="nswe")
        create_button(self, 4, 0, text="Seleccionar",
                      command=self._select_path_cache,
                      width=10, sticky="n")

    def save_settings(self):
        files_procces = self.entry_path_files.get()
        files_cache = self.entry_path_cache.get()
        config = {
            "files_procces": files_procces,
            "files_cache": files_cache
        }
        save_settings_fun(self.department, config)

    def load_settings(self):
        flag, self.settings = open_file_settings(filepath_settings)
        if "gui" in self.settings.keys() and flag:
            if self.department in self.settings["gui"].keys():
                try:
                    self.entry_path_files.set(self.settings["gui"][self.department]["files_procces"])
                    self.entry_path_cache.set(self.settings["gui"][self.department]["files_cache"])
                except KeyError:
                    print("No se encontró el archivo de configuración")
                    self.entry_path_files.set("img/files")
                    self.entry_path_cache.set("img/files")
            else:
                print("No se encontró el departamento")
        else:
            print("No se encontró el archivo de configuración")

    def _get_data_from_settings(self):
        if self.department not in self.settings["gui"].keys():
            return "files/files_fichaje", "files"
        try:
            files_procces = self.settings["gui"][self.department]["files_procces"]
            files_cache = self.settings["gui"][self.department]["files_cache"]
            return files_procces, files_cache
        except KeyError:
            return "files/files_fichaje", "files"

    def _select_path_file(self):
        path = select_path()
        if path is not None:
            self.entry_path_files.set(path)

    def _select_path_cache(self):
        path = select_path()
        if path is not None:
            self.entry_path_cache.set(path)


class SettingsChatbot(ttk.Frame):
    def __init__(self, master, settings, department, style_gui, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.master = master
        self.settings = settings
        self.department = department
        self.style_gui = style_gui
        self.sample_time = 5
        # ----------------Cantidad de chats-----------------
        frame_chats = ttk.Frame(self)
        frame_chats.grid(row=0, column=0, padx=10, pady=10)
        frame_chats.columnconfigure((0, 1), weight=1)
        ttk.Label(frame_chats, text="Cantidad de Chats para mostrar: ", font=("Arial", 14)).grid(
            row=0, column=0, padx=10, pady=(0, 10))
        self.entry_chats_max = ttk.StringVar()
        self.entry_chats_max.set("40")  # Valor inicial
        ttk.Entry(frame_chats, textvariable=self.entry_chats_max).grid(
            row=0, column=1, padx=10, pady=(0, 10))
        # ---------------------Rango de fechas----------------
        frame_dates = ttk.Frame(self)
        frame_dates.grid(row=1, column=0, padx=10, pady=10)
        frame_dates.columnconfigure((0, 1), weight=1)
        ttk.Label(frame_dates, text="Rango de Fechas", font=("Arial", 14)).grid(
            row=0, column=0, columnspan=2)
        ttk.Label(frame_dates, text="Fecha Inicial: ", font=("Arial", 14)).grid(
            row=1, column=0, padx=10, pady=(0, 10))
        ttk.Label(frame_dates, text="Fecha Final: ", font=("Arial", 14)).grid(
            row=1, column=1, padx=10, pady=(0, 10))
        self.start_date = ttk.DateEntry(frame_dates)
        self.start_date.grid(row=2, column=0, padx=10, pady=10)
        self.end_date = ttk.DateEntry(frame_dates)
        self.end_date.grid(row=2, column=1, padx=10, pady=10)
        # ----------tiempo de muestreo--------------
        frame_ts = ttk.Frame(self)
        frame_ts.grid(row=2, column=0, padx=10, pady=10)
        ttk.Label(frame_ts, text="Tiempo de Muestreo:", font=("Arial", 14)).grid(
            row=4, column=0, padx=10, pady=(0, 10), columnspan=3)
        self.label_ts_val = ttk.Label(frame_ts, text=int(self.sample_time),
                                      font=("Arial", 10))
        self.label_ts_val.grid(row=5, column=1, padx=10, pady=(0, 10))
        self.sampling_time = ttk.Scale(
            frame_ts, length=400, orient="horizontal", from_=1, to=59)
        self.sampling_time.set(self.sample_time)  # Valor inicial
        self.sampling_time.bind("<ButtonRelease-1>", self.update_val)
        self.sampling_time.grid(row=6, column=1, padx=10, pady=(0, 10))
        ttk.Label(frame_ts, text="1", font=("Arial", 10)).grid(
            row=6, column=0, padx=1, sticky="e")
        ttk.Label(frame_ts, text="59", font=("Arial", 10)).grid(
            row=6, column=2, padx=1, sticky="w")

    def update_val(self, e):
        self.label_ts_val.configure(text=int(e.widget.get()))

    def save_settings(self):
        max_chats = self.entry_chats_max.get()
        start_date = self.start_date.entry.get()
        end_date = self.end_date.entry.get()
        sampling_time = self.sampling_time.get()
        config = {
            "max_chats": max_chats,
            "start_date": start_date,
            "end_date": end_date,
            "sampling_time": sampling_time
        }
        save_settings_fun(self.department, config)

    def load_settings(self):
        flag, self.settings = open_file_settings(filepath_settings)
        if "gui" in self.settings.keys() and flag:
            if self.department in self.settings["gui"].keys():
                try:
                    self.entry_chats_max.set(self.settings["gui"][self.department]["max_chats"])
                    set_dateEntry_new_value(
                        self.start_date.master, self.start_date,
                        self.settings["gui"][self.department]["start_date"],
                        2, 0, 10, 10, "n"
                    )
                    set_dateEntry_new_value(
                        self.end_date.master, self.end_date,
                        self.settings["gui"][self.department]["end_date"],
                        2, 1, 10, 10, "n"
                    )
                    self.sampling_time.set(self.settings["gui"][self.department]["sampling_time"])
                except KeyError:
                    print("No se encontró el archivo de configuración")
                    self.entry_chats_max.set("40")
                    set_dateEntry_new_value(
                        self.start_date.master, self.start_date,
                        datetime.now(),
                        2, 0, 10, 10, "n"
                    )
                    set_dateEntry_new_value(
                        self.end_date.master, self.end_date,
                        datetime.now(),
                        2, 1, 10, 10, "n"
                    )
                    self.sampling_time.set(5)
            else:
                print("No se encontró el departamento")
        else:
            print("No se encontró el archivo de configuración")


class SettingsGeneral(ttk.Frame):
    def __init__(self, master, settings, department, style_gui, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        # self.columnconfigure((0, 1), weight=1)
        # -----------variables--------------------
        self.settings = settings
        self.department = department
        self.filepath = filepath_settings
        self.style_gui = style_gui
        # -------------widgets----------------
        themes = self.style_gui.theme_names()
        create_label(self, text="Tema: ", row=0, column=0, sticky="nswe",
                     font=("Arial", 14, "normal"))
        self.theme_selector = create_Combobox(self, row=0, column=1, values=themes,
                                              state="readonly", sticky="w")
        self.theme_selector.bind('<<ComboboxSelected>>',
                                 lambda event: self.style_gui.theme_use(self.theme_selector.get()))
        # ---------------initialization-----------
        self.stablish_sttings()

    def save_settings(self, department: str):
        theme = self.style_gui.theme_use()
        if "gui" not in self.settings.keys():
            self.settings["gui"] = {
                department: {
                    "theme": theme
                }
            }
        else:
            if department not in self.settings["gui"].keys():
                self.settings["gui"][department] = {
                    "theme": theme
                }
            else:
                self.settings["gui"][department]["theme"] = theme
        update_file_settings(self.filepath, self.settings)

    def load_settings(self, department: str):
        flag, self.settings = open_file_settings(filepath_settings)
        if "gui" in self.settings.keys() and flag:
            if department in self.settings["gui"].keys():
                self.style_gui.theme_use(self.settings["gui"][department]["theme"])
                self.theme_selector.set(self.settings["gui"][department]["theme"])
                print(f"Se cargó el tema: {self.settings['gui'][department]['theme']}")
            else:
                print("No se encontró el departamento")

    def stablish_sttings(self):
        if "gui" in self.settings.keys():
            if self.department in self.settings["gui"].keys():
                try:
                    self.style_gui.theme_use(self.settings["gui"][self.department]["theme"])
                    self.theme_selector.set(self.settings["gui"][self.department]["theme"])
                    print(f"Se cargó el tema: {self.settings['gui'][self.department]['theme']}")
                except KeyError:
                    print("No se encontró el tema, se establecera el por defecto")
                    self.theme_selector.current(0)
                    self.style_gui.theme_use(self.theme_selector.get())
            else:
                print("No se encontró el departamento")


class SettingsScreenAlmacen(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        self.master = master
        self.columnconfigure(0, weight=1)
        self._data = DataHandler()
        self.create_content()

    def create_content(self):
        content = ttk.Frame(self, style="bg.TFrame")
        content.columnconfigure(0, weight=1)
        content.grid(row=0, column=0, sticky="nswe")

        ttk.Label(
            content, text="Configuracion Almacen", style="bg.TLabel", font=("Arial Black", 18, "normal")
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            content,
            text="Importar registros multiples",
            style="bg.TLabel",
            font=("Arial", 14),
        ).grid(row=2, column=0, sticky="nswe", pady=(16, 0), padx=10)

        # Grid for upload files
        upload_file = ttk.Frame(content, style="bg.TFrame")
        upload_file.grid(row=3, column=0, sticky="nsew")
        upload_file.columnconfigure((0, 1, 2, 3), weight=1)

        # Button for upload products
        ttk.Label(upload_file, text="Insertar Inventario", style="bg.TLabel").grid(
            row=0, column=1, sticky="w", pady=(16, 0), padx=10
        )
        ttk.Button(
            upload_file, text="Seleccionar archivo", command=self.load_products
        ).grid(row=1, column=1, sticky="w", pady=(16, 0), padx=10)

        # Button for upload categories
        ttk.Label(
            upload_file,
            text="Insertar Categorias",
            style="bg.TLabel",
        ).grid(row=0, column=3, sticky="w", pady=(16, 0), padx=10)
        ttk.Button(
            upload_file,
            text="Seleccionar archivo",
            command=self.load_cateogires,
        ).grid(row=1, column=3, sticky="w", pady=(16, 0), padx=10)

        # Frame for message box
        message_box = ttk.Frame(content, style="bg.TFrame")
        message_box.grid(row=4, column=0, sticky="nsew")
        message_box.columnconfigure(0, weight=1)
        ttk.Label(message_box, text="Mensajes", style="bg.TLabel").grid(
            row=0, column=0, sticky="w", pady=(16, 0), padx=10
        )
        self.message_box = ttk.Label(message_box, text="", style="bg.TLabel")
        self.message_box.grid(row=1, column=0, sticky="w", pady=(16, 0), padx=10)

    def _message_box(self, title, message):
        self.message_box.config(text=f"{title}: {message}")

    def load_cateogires(self):
        file = filedialog.askopenfilename(
            parent=self,
            initialdir=os.getcwd(),
            title="Please select a directory",
            filetypes=[("CSV files", "*.csv")],
        )

        if not file:
            self._message_box("Categorias", "No se selecciono ningun archivo")
            return

        if (
            not file.lower().endswith(".csv")
            or os.path.basename(file) != "categorias.csv"
        ):
            self._message_box(
                "Categorias", "El archivo debe ser un .csv y llamarse categorias.csv"
            )
            return

        df = pd.read_csv(file, header=None)

        if len(df.columns) != 1:
            self._message_box(
                "Categorias",
                "El archivo debe contener 1 columna: nombre",
            )
            return

        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data.create_category(fila[0])
        self._message_box("Categorias", "Categorias cargadas correctamente")

    def load_products(self):
        file = filedialog.askopenfilename(
            parent=self,
            initialdir=os.getcwd(),
            title="Please select a directory",
            filetypes=[("CSV files", "*.csv")],
        )

        if not file:
            self._message_box("Inventario", "No se selecciono ningun archivo")
            return

        if (
            not file.lower().endswith(".csv")
            or os.path.basename(file) != "inventario.csv"
        ):
            self._message_box(
                "Inventario", "El archivo debe ser un .csv y llamarse inventario.csv"
            )
            return

        df = pd.read_csv(file, header=None)

        if len(df.columns) != 9:
            self._message_box(
                "Inventario",
                "El archivo debe contener 9 columnas: sku, nombre, udm, stock, minstock, maxstock, reorderPoint id_categoria, id_proveedor",
            )
            return

        for indice, fila in enumerate(df.values):
            if indice == 0:
                continue
            self._data.create_product(
                fila[0],
                fila[1],
                fila[2],
                fila[3],
                fila[7],
                fila[8],
            )
        self._message_box("Inventario", "Inventario cargados correctamente")
    
    def save_settings(self):
        pass
    
    def load_settings(self):
        pass
