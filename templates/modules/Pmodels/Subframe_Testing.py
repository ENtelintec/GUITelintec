import os

# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 05/jun./2024  at 16:03 $'

import json
import re

import ttkbootstrap as ttk

from static.extensions import filepath_settings
from templates.Functions_Pmodels import test_model_fichajes
from templates.Funtions_Utils import create_label, create_Combobox, create_button

days_of_week_dict = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5,
                     "Domingo": 6}
days_of_week_dict_reverse = {v: k for k, v in days_of_week_dict.items()}
months_dict = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
               "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12}
months_dict_reverse = {v: k for k, v in months_dict.items()}
events_dict = {"Faltas": "absence", "Atrasos": "lates", "Extras": "extra", "Primas": "prime"}


def read_files_models(directory_path: str):
    models = [[],[]]
    scalars = []
    data_test = []
    # check file in directory
    model_pattern = ".*model.*\.keras"
    scalar_pattern = ".*scalar.*\.pkl"
    data_pattern = ".*last_vals.*\.pkl"
    files = os.listdir(directory_path)
    for file in files:
        # check regex pattehr in name
        if re.match(model_pattern, file):
            models[0].append(file) if "class" in file else models[1].append(file)
        elif re.match(scalar_pattern, file):
            scalars.append(file)
        elif re.match(data_pattern, file):
            data_test.append(file)
    return models, scalars, data_test


class TestingFrame(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        settings = json.load(open(filepath_settings))
        self.files_dir = settings['pmodels_files']
        self.svar_day = ttk.StringVar()
        self.svar_month = ttk.StringVar()
        self.svar_threshold = ttk.StringVar()
        self.svar_threshold_value = ttk.IntVar()
        # ----------------------------------------------create title--------------------------------------------------
        create_label(self, 0, 0, text="Testing", font=("Helvetica", 24, "bold"), sticky="n")
        # ----------------------------------------------------create inputs----------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, padx=5, pady=5, sticky="nswe")
        frame_inputs.columnconfigure((0, 1, 2), weight=1)
        # event selector -------------------------------------------------------
        create_label(frame_inputs, row=0, column=0, text="Evento:")
        self.selector_event = create_Combobox(frame_inputs, row=1, column=0,
                                              values=["Faltas", "Atrasos", "Extras", "Primas"], state="readonly",
                                              sticky="n")
        self.selector_event.bind("<<ComboboxSelected>>", self.update_threshold)
        # parameters for testing selector----------------------------------------------
        create_label(frame_inputs, 2, 0, text="Día:")
        days_week = list(days_of_week_dict.keys())
        create_Combobox(frame_inputs, row=3, column=0, values=days_week, state="readonly", textvariable=self.svar_day,
                        sticky="n")
        create_label(frame_inputs, row=2, column=1, text="Mes:")
        create_Combobox(frame_inputs, row=3, column=1, values=list(range(1, 13)), state="readonly",
                        textvariable=self.svar_month, sticky="n")
        create_label(frame_inputs, row=2, column=2, textvariable=self.svar_threshold)
        scale = ttk.Scale(frame_inputs, from_=1, to=100, orient=ttk.HORIZONTAL, length=100, bootstyle="primary",
                          command=self.update_scale_value)
        scale.grid(row=3, column=2, padx=5, pady=5, sticky="n")
        scale.set(90)
        # data models for testing selector -------------------------------------------
        models, scalars, data_test = read_files_models(self.files_dir)
        create_label(frame_inputs, 2, 0, text="Modelo:")
        self.selector_model_class = create_Combobox(frame_inputs, row=5, column=0, values=models[0], state="readonly",
                                                    sticky="nswe")
        self.selector_model_linear = create_Combobox(frame_inputs, row=6, column=0, values=models[1], state="readonly",
                                                     sticky="nswe")
        self.selector_model_class.bind("<<ComboboxSelected>>", self.update_model)
        self.selector_model_linear.bind("<<ComboboxSelected>>", self.update_model)
        create_label(frame_inputs, 4, 1, text="Escalar:")
        self.selector_scalar = create_Combobox(frame_inputs, row=5, column=1, values=scalars, state="readonly",
                                               sticky="nswe")
        create_label(frame_inputs, 4, 2, text="Datos:")
        self.selector_data = create_Combobox(frame_inputs, row=5, column=2, values=data_test, state="readonly",
                                             sticky="nswe")
        # ----------------------------------buttons-------------------------------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, padx=5, pady=5, sticky="nswe")
        frame_buttons.columnconfigure((0, 1), weight=1)
        create_button(frame_buttons, 0, 0, text="Predecir", command=self.test_model, sticky="n")
        create_button(frame_buttons, 0, 1, text="Actualizar", command=self.read_files, sticky="n")
        frame_show_info = ttk.Frame(self)
        frame_show_info.grid(row=3, column=0, padx=5, pady=5, sticky="nswe")
        frame_show_info.columnconfigure(0, weight=1)
        self.txt_info = ttk.Text(frame_show_info, height=10, width=100)
        self.txt_info.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")

    def read_files(self):
        models, scalars, data_test = read_files_models(self.files_dir)
        self.selector_model_class["values"] = models[0]
        self.selector_model_linear["values"] = models[1]
        self.selector_scalar["values"] = scalars
        self.selector_data["values"] = data_test
        self.selector_model_class.current(0)
        self.selector_model_linear.current(0)
        self.selector_scalar.current(0)
        self.selector_data.current(0)

    def test_model(self):
        file_model = self.selector_model_class.get()
        file_scalar = self.selector_scalar.get()
        file_data = self.selector_data.get()
        if "No hay" in file_model or "No hay" in file_scalar or "No hay" in file_data:
            print("Invalid operation, data missing.")
            return
        if "class" in file_model:
            file_model_secondary = file_model.replace("class", "linear")
        else:
            file_model_secondary = file_model.replace("linear", "class")
        day_of_week = days_of_week_dict[self.svar_day.get()]
        month = int(self.svar_month.get())
        filepath_model_class = os.path.join(self.files_dir, file_model)
        filepath_scalar = os.path.join(self.files_dir, file_scalar)
        filepath_out_vectors = os.path.join(self.files_dir, file_data)
        filepath_model_linear = os.path.join(self.files_dir, file_model_secondary)
        y_pred, x_news, error, x_emps = test_model_fichajes(filepath_model_class, filepath_scalar, filepath_out_vectors,
                                                            day_of_week, month,
                                                            types_model=(1, 2), filepath_model_linear=filepath_model_linear)
        threshold = self.svar_threshold_value.get() / 100.0
        print(threshold)
        msg = ""
        counter = 0
        print(f"posibles dias tarde: {counter}")
        for index, item in enumerate(y_pred[0]):
            if item > threshold and y_pred[1][index] > 0.25:
                counter += 1
                msg += (f"El empleado con ID {int(x_emps[index, 0])} es posible que tenga un evento el dia {days_of_week_dict_reverse[day_of_week]} "
                        f"en el mes {months_dict_reverse[month]}. Con una probabiliad {str(round(item[0], 2))} y un valor de {str(round(y_pred[1][index][0], 2))}\n")
        print(f"posibles dias con evento: {counter}")
        self.txt_info.delete("1.0", "end")
        self.txt_info.insert("end", msg)

    def update_scale_value(self, event):
        self.svar_threshold.set(f"Estricto: {int(float(event))}%")
        self.svar_threshold_value.set(int(float(event)))

    def update_threshold(self, event):
        event_txt = event.widget.get()
        models, scalars, data_test = read_files_models(self.files_dir)
        models[0] = [item for item in models[0] if events_dict[event_txt] in item]
        models[1] = [item for item in models[1] if events_dict[event_txt] in item]
        scalars = [item for item in scalars if events_dict[event_txt] in item]
        data_test = [item for item in data_test if events_dict[event_txt] in item]
        models[0] = models[0] if len(models[0]) > 0 else ["No hay modelos para ese evento"]
        models[1] = models[1] if len(models[1]) > 0 else ["No hay modelos para ese evento"]
        scalars = scalars if len(scalars) > 0 else ["No hay escalas para ese evento"]
        data_test = data_test if len(data_test) > 0 else ["No hay datos para ese evento"]
        self.selector_model_class["values"] = models[0]
        self.selector_model_linear["values"] = models[1]
        self.selector_scalar["values"] = scalars
        self.selector_data["values"] = data_test
        self.selector_model_class.current(0)
        self.selector_model_linear.current(0)
        self.selector_scalar.current(0)
        self.selector_data.current(0)
        

    def update_model(self, event):
        filename = event.widget.get()
        if "class" in filename:
            self.selector_model_linear.set(filename.replace("class", "linear"))
        else:
            self.selector_model_class.set(filename.replace("linear", "class"))
