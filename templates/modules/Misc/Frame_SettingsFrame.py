from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import ttkbootstrap as ttk

from static.extensions import filepath_settings
from templates.Functions_Files import open_file_settings, update_file_settings
from templates.Funtions_Utils import create_label, create_Combobox, create_button, set_dateEntry_new_value

IMG_PATH = Path('./img')


def select_path():
    """
    Función para seleccionar una carpeta de archivos
    :return:
    """
    path = filedialog.askdirectory()
    print(path)
    return path


class SettingsFrameGUI(ttk.Frame):
    def __init__(self, master, style_gui, department=None, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.filepath = filepath_settings
        self.master = master
        self.style_gui = ttk.Style() if style_gui is None else style_gui
        self.department = department
        flag, self.settings = open_file_settings(filepath_settings) if setting is None else (True, setting)
        create_label(self, text="Configuraciones", row=0, column=0, sticky="nswe",
                     font=("Arial", 20, "bold"))
        self.settings_frame = SettingsGeneral(self, self.settings, self.department, self.style_gui)
        self.settings_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        match self.department:
            case w if w in ["RRHH", "rrhh"]:
                self.secondary_frame = SettingsRRHH(self, self.settings, self.department, self.style_gui)
            case "Chatbot":
                self.secondary_frame = SettingsChatbot(self, self.settings, self.department, self.style_gui)
            case _:
                self.secondary_frame = None
        if self.secondary_frame is not None:
            self.secondary_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        # -------------------------btns--------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.columnconfigure((0, 1), weight=1)
        frame_btns.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        create_button(frame_btns, text="Guardar", command=self.save_settings_master,
                      width=10, row=0, column=0, sticky="n")
        create_button(frame_btns, text="Cargar", command=self.load_settings_master,
                      width=10, row=0, column=1, sticky="n")

    def save_settings_master(self):
        self.settings_frame.save_settings(self.department)
        if self.secondary_frame is not None:
            self.secondary_frame.save_settings()

    def load_settings_master(self):
        self.settings_frame.load_settings(self.department)
        if self.secondary_frame is not None:
            self.secondary_frame.load_settings()


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
                     font=("Arial", 20, "bold"))
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
        if "gui" not in self.settings.keys():
            self.settings["gui"] = {
                self.department: {
                    "files_procces": files_procces,
                    "files_cache": files_cache
                }
            }
        else:
            if self.department not in self.settings["gui"].keys():
                self.settings["gui"][self.department] = {
                    "files_procces": files_procces,
                    "files_cache": files_cache
                }
            else:
                self.settings["gui"][self.department]["files_procces"] = files_procces
                self.settings["gui"][self.department]["files_cache"] = files_cache
        update_file_settings(filepath_settings, self.settings)

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
        if self.department in self.settings["gui"].keys():
            try:
                files_procces = self.settings["gui"][self.department]["files_procces"]
                files_cache = self.settings["gui"][self.department]["files_cache"]
                return files_procces, files_cache
            except KeyError:
                return "img/files", "img/files"
        else:
            return "img/files", "img/files"

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
        ttk.Label(frame_chats, text="Cantidad de Chats para mostrar: ", font=("Arial", 16)).grid(
            row=0, column=0, padx=10, pady=(0, 10))
        self.entry_chats_max = ttk.StringVar()
        self.entry_chats_max.set("40")  # Valor inicial
        ttk.Entry(frame_chats, textvariable=self.entry_chats_max).grid(
            row=0, column=1, padx=10, pady=(0, 10))
        # ---------------------Rango de fechas----------------
        frame_dates = ttk.Frame(self)
        frame_dates.grid(row=1, column=0, padx=10, pady=10)
        frame_dates.columnconfigure((0, 1), weight=1)
        ttk.Label(frame_dates, text="Rango de Fechas", font=("Arial", 16)).grid(
            row=0, column=0, columnspan=2)
        ttk.Label(frame_dates, text="Fecha Inicial: ", font=("Arial", 16)).grid(
            row=1, column=0, padx=10, pady=(0, 10))
        ttk.Label(frame_dates, text="Fecha Final: ", font=("Arial", 16)).grid(
            row=1, column=1, padx=10, pady=(0, 10))
        self.start_date = ttk.DateEntry(frame_dates)
        self.start_date.grid(row=2, column=0, padx=10, pady=10)
        self.end_date = ttk.DateEntry(frame_dates)
        self.end_date.grid(row=2, column=1, padx=10, pady=10)
        # ----------tiempo de muestreo--------------
        frame_ts = ttk.Frame(self)
        frame_ts.grid(row=2, column=0, padx=10, pady=10)
        ttk.Label(frame_ts, text="Tiempo de Muestreo:", font=("Arial", 16)).grid(
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
        if "gui" not in self.settings.keys():
            self.settings["gui"] = {
                self.department: {
                    "max_chats": max_chats,
                    "start_date": start_date,
                    "end_date": end_date,
                    "sampling_time": sampling_time,
                }
            }
        else:
            if self.department not in self.settings["gui"].keys():
                self.settings["gui"][self.department] = {
                    "max_chats": max_chats,
                    "start_date": start_date,
                    "end_date": end_date,
                    "sampling_time": sampling_time,
                }
            else:
                self.settings["gui"][self.department]["max_chats"] = max_chats
                self.settings["gui"][self.department]["start_date"] = start_date
                self.settings["gui"][self.department]["end_date"] = end_date
                self.settings["gui"][self.department]["sampling_time"] = sampling_time
        flag, error = update_file_settings(filepath_settings, self.settings)
        return flag

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
