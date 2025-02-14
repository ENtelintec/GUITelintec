# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 13/may./2024  at 16:40 $"

import json
import os
from shutil import copyfile
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.dialogs import Messagebox

from static.constants import quizzes_temp_pdf
from templates.controllers.misc.tasks_controller import get_all_tasks_by_status
from templates.Functions_GUI_Utils import (
    create_label,
    create_button,
    calculate_results_quizzes,
)
from templates.misc.Functions_Files import (
    get_data_encuesta,
    extract_data_encuesta,
    create_report_encuesta,
)

dict_keys = {
    "name_emp": "Empleado",
    "date": "Fecha",
    "interviewer": "Entrevistador",
    "ID_emp": "ID",
    "position": "Cargo",
    "admision": "Admision",
    "departure": "Salida",
    "departure_reason": "Motivo de salida",
    "evaluated_emp": "Evaluado",
    "pos_evaluator": "Posicion Evaluador",
    "evaluated_emp_ID": "ID Evaluado",
    "type_quizz": "Tipo de Quiz",
}


def get_key_display(key: str):
    try:
        return dict_keys[key]
    except KeyError:
        return key


def create_data_for_table(quizzes_data):
    columns = (
        "Nombre",
        "ID",
        "Estado",
        "Nombre del Quiz",
        "Evaluador",
        "Fecha",
        "Data RAW",
        "Body",
    )
    data = []
    for item in quizzes_data:
        id_t, body, data_raw, timestamp = item
        body = json.loads(body)
        data_raw = json.loads(data_raw)
        data.append(
            (
                body["metadata"]["name_emp"],
                body["metadata"]["ID_emp"],
                "Completado" if body["status"] == 1 else "Pendiente",
                body["metadata"]["type_quizz"],
                body["metadata"]["interviewer"],
                body["metadata"]["date"],
                json.dumps(data_raw),
                json.dumps(body),
            )
        )
    return data, columns


class ViewQuizz(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self._current_data_raw = None
        self._current_body = None
        self.columnconfigure(0, weight=1)
        # -------------------------------variables------------------------------
        self.settings = kwargs.get("settings")
        self._svar_info = ttk.StringVar()
        self.style_gui = kwargs["style_gui"]
        self.selectors = None
        self.quizzes_data = kwargs.get("data", {}).get("encuestas", {}).get("tasks", [])
        # ------------title------------------------------
        create_label(self, 0, 0, text="Revisión de Quizzes", font=("Helvetica", 20))
        # -------------------create widgets--------------------------------------
        self.frame_selectors = ttk.Frame(self)
        self.frame_selectors.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_selectors.columnconfigure(0, weight=1)
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, padx=10, pady=10, sticky="nswe")
        frame_buttons.columnconfigure((0, 1), weight=1)
        self.selectors = self.create_table_selector(self.frame_selectors)
        self.text_info = self.create_buttons(frame_buttons)

    def create_table_selector(self, master):
        self.selectors.destroy() if self.selectors is not None else None
        data, columns = create_data_for_table(self.quizzes_data)
        coldata = []
        for column in columns:
            if "Fecha" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "ID" in column:
                coldata.append({"text": column, "stretch": False, "width": 50})
            elif "Fecha" in column:
                coldata.append({"text": column, "stretch": False, "width": 80})
            else:
                coldata.append({"text": column, "stretch": True})
        table = Tableview(
            master,
            coldata=coldata,
            rowdata=data,
            height=10,
            autofit=False,
            paginated=True,
            searchable=False,
        )
        table.grid(row=0, column=0, sticky="nswe", padx=(5, 30))
        table.view.bind("<Double-1>", self.on_double_click_quizz)
        columns_header = table.get_columns()
        for item in columns_header:
            if item.headertext in ["Data RAW"]:
                item.hide()
        return table

    def create_buttons(self, master):
        txt = ttk.ScrolledText(master, height=20, width=60, wrap=ttk.WORD)
        txt.grid(row=0, column=0, padx=5, pady=5, rowspan=4, sticky="nswe")
        create_button(
            master, 0, 1, text="Abrir PDF", command=self.view_pdf_action, sticky="n"
        )
        create_button(
            master,
            1,
            1,
            text="Generar PDF",
            command=self.create_pdf_action,
            sticky="n",
            bootstyle="warning",
        )
        create_button(
            master, 2, 1, text="Actualizar", command=self.update_action, sticky="n"
        )
        # create_button(
        #     master,
        #     3,
        #     1,
        #     text="Subir archivo",
        #     command=self.upload_file,
        #     sticky="n",
        #     bootstyle="secondary",
        # )
        return txt

    def on_double_click_quizz(self, event):
        item = event.widget.selection()[0]
        item_data = event.widget.item(item, "values")
        print("body: ", type(item_data[-1]))
        print("raw: ", type(item_data[-2]))
        self._current_body = json.loads(item_data[-1])
        self._current_data_raw = json.loads(item_data[-2])
        self.display_info_file()

    def display_info_file(self):
        self.text_info.delete("1.0", "end")
        for k, v in self._current_body["metadata"].items():
            self.text_info.insert("end", f"{get_key_display(k)} : ", "key")
            self.text_info.insert("end", f"{v}\n", "value")
        self.text_info.tag_config(
            "key", foreground=self.style_gui.colors.get("warning")
        )
        self.text_info.tag_config("value", foreground=self.style_gui.colors.get("fg"))

    def view_pdf_action(self):
        if os.name == "nt":
            dir_name = os.path.dirname(quizzes_temp_pdf)
            try:
                os.startfile(os.path.join(dir_name, os.path.basename(quizzes_temp_pdf)))
            except FileNotFoundError:
                Messagebox.show_error(
                    "No se ha creado el archivo pdf, pruebe a generarlo primero.",
                    "Error al abrir el archivo",
                )
        else:
            print("Not running on Windows")

    def create_pdf_action(self):
        if self._current_data_raw is None:
            Messagebox.show_error("No se ha seleccionado un archivo", "Error")
            return
        msg = "Esta seguro que desea crear el pdf?"
        answer = Messagebox.show_question(title="Confirmacion", message=msg)
        if answer == "No":
            return
        path = filedialog.askdirectory()
        json_dict = self._current_body
        file_out = quizzes_temp_pdf
        path += f"/{json_dict['metadata']['name_emp'].replace(' ', '')}_{json_dict['metadata']['date'].replace('/', '-')}_type_{json_dict['metadata']['type_quizz']}.pdf"
        tipo_op = json_dict["metadata"]["type_quizz"]
        from static.FramesClasses import dict_typer_quizz_generator

        generator = dict_typer_quizz_generator[tipo_op]
        generator(
            self._current_data_raw,
            None,
            file_out,
            json_dict["metadata"]["name_emp"],
            json_dict["metadata"]["position"],
            "terminal",
            json_dict["metadata"]["admision"],
            json_dict["metadata"]["departure"],
            json_dict["metadata"]["date"],
            json_dict["metadata"]["interviewer"],
        )
        # copy the file to path
        copyfile(file_out, path)
        Messagebox.show_info(f"PDF creado en: {path}", "PDF creado")

    def update_action(self):
        flag, error, tasks = get_all_tasks_by_status(status=-1, title="quizz")
        self.quizzes_data = tasks if flag else self.quizzes_data
        self.selectors = self.create_table_selector(self.frame_selectors)

    def upload_file(self):
        # select excel
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Comma separated values", "*.csv"),
                ("Excel", "*.xls"),
                ("Excel", "*.xlsx"),
            ]
        )
        if file_path == "":
            return
        # file_path = "files/NOM-035 STPS 2018.csv"
        # file_path = "files/NOM-035 STPS 2018.csv"
        data, df = get_data_encuesta(file_path)
        dict_quizz_list, metadata_list = extract_data_encuesta(data)
        dict_results_list = []
        msg = ""
        msg += f"Se han encontrado {len(dict_quizz_list)} encuestas"
        for dict_quizz, metadata in zip(dict_quizz_list, metadata_list):
            dict_results = calculate_results_quizzes(dict_quizz, 2)
            dict_results_list.append(dict_results)
            msg += "------------------------------------------Encuesta--------------------------------------"
            msg += "\n"
            msg += "---------------------------------------------------------------------------------------"
            msg += "\n -------------Resultados de la encuesta-----------"
            for key, value in dict_results.items():
                if "detail" in key:
                    continue
                if isinstance(value, dict):
                    msg += f"\n--{key} :"
                    for k, v in value.items():
                        msg += f"\n---{k} : {v}"
                else:
                    msg += f"\n-{key} : {value}"
            msg += "\n -------------Informacion en el archivo-----------"
            for index, key in enumerate(metadata.keys()):
                if index < 12:
                    msg += f"\n-{key} : {metadata[key]}"
                else:
                    break
        self.text_info.delete("1.0", "end")
        self.text_info.insert("end", msg)
        path_out = create_report_encuesta(metadata_list, 2, dict_results_list)
        print("report in: ", path_out)
