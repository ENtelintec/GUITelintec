import json
import tkinter as tk
from tkinter import StringVar

import customtkinter as ctk
# from tkcalendar import DateEntry
import ttkbootstrap as ttk
from pathlib import Path
from ttkbootstrap.constants import *
from ttkbootstrap.style import Bootstyle

filepath_settings = "../files/settings.json"
IMG_PATH = Path('./img')


class ChatSettingsApp(ctk.CTkFrame):
    def __init__(self, master, father=None, filepath=filepath_settings, *args, **kwargs):
        super().__init__(master, fg_color="#040546", *args, **kwargs)
        self.filepath = filepath
        self.master = father
        # Title label
        cf = CollapsingFrame(master)
        cf.grid(row=0, column=0, columnspan=6, padx=1, pady=1, sticky="nsew")
        group_1 = ttk.Frame(cf, padding=10)
        # Cantidad de chats
        max_chats_label = ctk.CTkLabel(group_1, text="Cantidad de Chats para mostrar: ",
                                       font=("Arial", 16), text_color="white",
                                       fg_color="transparent")
        self.entry_chats_max = tk.StringVar()
        self.entry_chats_max.set("40")  # Valor inicial
        self.max_chats_entry = ctk.CTkEntry(group_1, textvariable=self.entry_chats_max)
        max_chats_label.grid(row=0, column=0, padx=10, pady=(0, 10))
        self.max_chats_entry.grid(row=0, column=1, padx=10, pady=(0, 10))
        cf.add(group_1, title="Cantidad de Chats")
        # Rango de fechas
        group_2 = ttk.Frame(cf, padding=10)
        date_range_label = ctk.CTkLabel(group_2, text="Rango de Fechas: ",
                                        font=("Arial", 16), text_color="white")

        date_init_label = ctk.CTkLabel(group_2, text="Fecha Inicial: ",
                                       font=("Arial", 16), text_color="white")
        date_end_label = ctk.CTkLabel(group_2, text="Fecha Final: ",
                                      font=("Arial", 16), text_color="white")
        self.start_date = ttk.DateEntry(group_2)
        self.end_date = ttk.DateEntry(group_2)
        date_range_label.grid(row=0, column=0, padx=10, pady=(0, 10))
        date_init_label.grid(row=0, column=1, padx=10, pady=(0, 10))
        date_end_label.grid(row=0, column=2, padx=10, pady=(0, 10))
        self.start_date.grid(row=1, column=1, padx=10, pady=(0, 10))
        self.end_date.grid(row=1, column=2, padx=10, pady=(0, 10))
        cf.add(group_2, title="Rango de Fechas")

        group_3 = ttk.Frame(cf, padding=10)
        # Widget para el tiempo de muestreo
        self.label_ts_val = ttk.Label(group_3, text=int(self.master.sample_time),
                                      font=("Arial", 10))
        sampling_time_label = ctk.CTkLabel(group_3, text="Tiempo de Muestreo:",
                                           font=("Arial", 25), text_color="white")
        self.sampling_time = ttk.Scale(group_3, length=400, orient="horizontal",
                                       from_=1, to=59, command=self.update_val)
        self.sampling_time.set(self.master.sample_time)  # Valor inicial
        self.sampling_time.bind("<ButtonRelease-1>", self.update_var)
        label_ts_ini = ttk.Label(group_3, text="1", font=("Arial", 10))
        label_ts_end = ttk.Label(group_3, text="59", font=("Arial", 10))
        sampling_time_label.grid(row=4, column=0, padx=10, pady=(0, 10))
        label_ts_ini.grid(row=4, column=1, padx=10, pady=(0, 10))
        self.sampling_time.grid(row=4, column=2, padx=10, pady=(0, 10))
        self.label_ts_val.grid(row=5, column=2, padx=10, pady=(0, 10))
        label_ts_end.grid(row=4, column=3, padx=10, pady=(0, 10))

        # Widget para tamaño de letra
        self.font_size = ttk.IntVar()
        self.font_size.set(12)  # Tamaño de letra inicial
        self.label = ctk.CTkLabel(group_3, text="Texto de ejemplo",
                                  font=("Arial", self.font_size.get()),
                                  text_color="white")
        self.font_size_scale = tk.Scale(group_3, from_=8, to=24,
                                        variable=self.font_size,
                                        orient="horizontal", label="Tamaño de Letra",
                                        font=("Arial", 20), length=400)
        apply_button = ctk.CTkButton(group_3, text="Aplicar Tamaño", command=self.update_font)
        self.label.grid(row=0, column=0, columnspan=3, padx=10, pady=(0, 10))
        self.font_size_scale.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10))
        apply_button.grid(row=2, column=0, padx=10, pady=(0, 10), columnspan=3)
        cf.add(group_3, title="Geometria")

        # Botón para guardar la configuración (opcional)
        save_button = ctk.CTkButton(master, text="Guardar Configuración")
        save_button.grid(row=8, column=0, padx=10, pady=10)
        save_button.configure(command=self.save_settings)
        load_button = ctk.CTkButton(master, text="Cargar Configuración")
        load_button.grid(row=8, column=2, padx=10, pady=10)
        load_button.configure(command=self.update_settings)

    def update_var(self, e):
        print("sampling time: ", int(self.sampling_time.get()))
        if self.master is not None:
            self.master.update_variable(self.sampling_time.get(), 1,
                                        self.entry_chats_max.get())

    def update_val(self, e):
        self.label_ts_val.configure(text=int(self.sampling_time.get()))

    def save_settings(self):
        max_chats = self.max_chats_entry.get()
        start_date = self.start_date.entry.get()
        end_date = self.end_date.entry.get()
        sampling_time = self.sampling_time.get()
        with open(self.filepath, "w") as f:
            json.dump(
                {
                    "max_chats": max_chats,
                    "start_date": start_date,
                    "end_date": end_date,
                    "sampling_time": sampling_time,
                },
                f,
            )
        print("Configuración Guardada:")
        print("Cantidad Máxima de Chats:", max_chats)
        print("Rango de Fechas:", start_date, " - ", end_date)
        print("Tiempo de Muestreo:", sampling_time, "minutos")

    def update_settings(self):
        with open(self.filepath, "r") as f:
            settings = json.load(f)
        print("Configuración Cargada:")
        print("Cantidad Máxima de Chats:", settings["max_chats"])
        print("Rango de Fechas:", settings["start_date"], " - ", settings["end_date"])
        print("Tiempo de Muestreo:", settings["sampling_time"], "minutos")
        # self.max_chats_entry.insert(0, settings["max_chats"])

    def update_font(self):
        # new_size = self.font_size.get()
        #  self.label.configure(font=("Arial", new_size))
        self.update_font_size()

    def update_font_size(self):
        new_size = self.font_size.get()
        labels = [self.label]  # Add more labels here if needed
        for label in labels:
            label.configure(font=("Arial", new_size))

    def get_date_start(self):
        # Obtener el valor de self.start_date
        return self.start_date.entry.get()

    def get_date_end(self):
        # Obtener el valor de self.end_date
        return self.end_date.entry.get()

    def get_max_chats(self):
        return self.max_chats_entry.get()

    def get_sampling_time(self):
        return self.sampling_time.get()


class CollapsingFrame(ttk.Frame):
    """A collapsible frame widget that opens and closes with a click."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.cumulative_rows = 0

        # widget images
        self.images = [
            ttk.PhotoImage(file=IMG_PATH / 'arrow__1_a.png'),
            ttk.PhotoImage(file=IMG_PATH / 'arrow_2_b.png')
        ]

    def add(self, child, title="", bootstyle=DARK, **kwargs):
        """Add a child to the collapsible frame

        Parameters:

            child (Frame):
                The child frame to add to the widget.

            title (str):
                The title appearing on the collapsible section header.

            bootstyle (str):
                The style to apply to the collapsible section header.

            **kwargs (Dict):
                Other optional keyword arguments.
        """
        if child.winfo_class() != 'TFrame':
            return

        style_color = Bootstyle.ttkstyle_widget_color(bootstyle)
        frm = ttk.Frame(self, bootstyle=style_color)
        frm.grid(row=self.cumulative_rows, column=0, sticky=EW)

        # header title
        header = ttk.Label(
            master=frm,
            text=title,
            bootstyle=(style_color, INVERSE),
            font=("Arial", 20)
        )
        if kwargs.get('textvariable'):
            header.configure(textvariable=kwargs.get('textvariable'))
        header.pack(side=LEFT, fill=BOTH, padx=10)

        # header toggle button
        def _func(c=child):
            return self._toggle_open_close(c)

        btn = ttk.Button(
            master=frm,
            image=self.images[0],
            bootstyle=style_color,
            command=_func
        )
        btn.pack(side=RIGHT)

        # assign toggle button to child so that it can be toggled
        child.btn = btn
        child.grid(row=self.cumulative_rows + 1, column=0, sticky=NSEW)

        # increment the row assignment
        self.cumulative_rows += 2

    def _toggle_open_close(self, child):
        """Open or close the section and change the toggle button
        image accordingly.

        Parameters:

            child (Frame):
                The child element to add or remove from grid manager.
        """
        if child.winfo_viewable():
            child.grid_remove()
            child.btn.configure(image=self.images[1])
        else:
            child.grid()
            child.btn.configure(image=self.images[0])


if __name__ == "__main__":
    app = ChatSettingsApp()
    app.mainloop()
