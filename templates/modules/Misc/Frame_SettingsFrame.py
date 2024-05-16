from pathlib import Path

import ttkbootstrap as ttk

from static.extensions import filepath_settings
from templates.Functions_Files import open_file_settings
from templates.Funtions_Utils import create_label, create_button
from templates.modules.Misc.SubFrame_Settings import SettingsRRHH, SettingsChatbot, SettingsGeneral, \
    SettingsScreenAlmacen

IMG_PATH = Path('./img')
avaliable_settings_frame = {
    "general": SettingsGeneral,
    "rrhh": SettingsRRHH,
    "chatbot": SettingsChatbot,
    "almacen":  SettingsScreenAlmacen
}


class SettingsFrameGUI(ttk.Frame):
    def __init__(self, master, style_gui, department=None, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.filepath = filepath_settings
        self.master = master
        self.style_gui = ttk.Style() if style_gui is None else style_gui
        self.department = department
        # --------------------------main frame----------------------------------
        flag, self.settings = open_file_settings(filepath_settings) if setting is None else (True, setting)
        create_label(self, text="Configuraciones", row=0, column=0, sticky="nswe",
                     font=("Arial", 20, "bold"))
        self.settings_frame = avaliable_settings_frame["general"](self, self.settings, self.department,
                                                                  self.style_gui)
        self.settings_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        # -------------------------btns--------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.columnconfigure((0, 1), weight=1)
        frame_btns.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        create_button(frame_btns, text="Guardar", command=self.save_settings_master,
                      width=10, row=0, column=0, sticky="n")
        create_button(frame_btns, text="Cargar", command=self.load_settings_master,
                      width=10, row=0, column=1, sticky="n")
        # -------------------------secondary frames-----------------------------
        print(kwargs["permissions"])
        index = 3
        self.secondary_frames = []
        for permission in kwargs["permissions"].values():
            key_val = permission.split(".")[-1]
            if key_val.lower() in avaliable_settings_frame.keys():
                secondary_frame = avaliable_settings_frame[key_val.lower()](self, self.settings, self.department,
                                                                            self.style_gui)
                secondary_frame.grid(row=index, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
                self.secondary_frames.append(secondary_frame)
                index += 1

    def save_settings_master(self):
        self.settings_frame.save_settings(self.department)
        if len(self.secondary_frames) >= 0:
            for frame in self.secondary_frames:
                frame.save_settings()

    def load_settings_master(self):
        self.settings_frame.load_settings(self.department)
        if len(self.secondary_frames) >= 0:
            for frame in self.secondary_frames:
                frame.load_settings()
