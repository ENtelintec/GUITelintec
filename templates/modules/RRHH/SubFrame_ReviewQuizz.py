import os
  # -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 13/may./2024  at 16:40 $'

import json

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.dialogs import Messagebox

from templates.Functions_AuxFiles import load_quizzes_names
from templates.Funtions_Utils import create_label, create_button
from templates.PDFGenerator import create_pdf_quizz_salida, create_pdf__quizz_nor035_v1, \
    create_pdf_quizz_nor035_50_plus, create_quizz_clima_laboral, create_quizz_eva_360

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
    "type_q": "Tipo de Quiz"
}


dict_typer_quizz_generator = {
    0: create_pdf_quizz_salida,
    1: create_pdf__quizz_nor035_v1,
    2: create_pdf_quizz_nor035_50_plus,
    3: create_quizz_clima_laboral,
    4: create_quizz_eva_360
}


def get_key_display(key: str):
    try:
        return dict_keys[key]
    except KeyError:
        return key


def create_data_for_table(pdf_files, json_files, path):
    # {metadata: {'name_emp': 'ALEJANDRO REGINO RUIZ ORTIZ ', 'date': '2024-05-13', 'interviewer': 'EDISSON ANDRES  NAULA DUCHI',
    #  'ID_emp': 1, 'position': 'NONE', 'admision': '2023-11-13', 'departure': '2024-03-27', 'departure_reason': '',
    #  'evaluated_emp': 'ALEJANDRO REGINO RUIZ ORTIZ ', 'pos_evaluator': 'Autoevaluación', 'evaluated_emp_ID': 1,
    #  'type_q': 0}}
    columns = ("Nombre", "ID", "Nombre del Quiz", "Evaluador", "Fecha", "Archivo PDF", "Archivo RAW")
    data = []
    for json_name in json_files:
        file = json.load(open(path + json_name, "r"))
        name_emp = file["metadata"]["name_emp"]
        row = [name_emp, file["metadata"]["evaluated_emp_ID"], file["metadata"]["title"],
               file["metadata"]["interviewer"], file["metadata"]["date"]]
        name_emp = name_emp.replace(" ", "")
        pdf_name_to_add = "No se encuentra el pdf"
        for pdf_name in pdf_files:
            if name_emp in pdf_name:
                pdf_name_to_add = pdf_name
                break
        row.append(pdf_name_to_add)
        row.append(json_name)
        data.append(row)
    return data, columns


class ViewQuizz(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        # -------------------------------variables------------------------------
        self.settings = kwargs.get('settings')
        self._svar_info = ttk.StringVar()
        self._pdf_file_selected = None
        self._json_file_selected = None
        self.style_gui = kwargs["style_gui"]
        self.selectors = None
        # ------------title------------------------------
        create_label(self, 0, 0, text="Revisión de Quizzes", font=("Helvetica", 20))
        self.names_files_pdf, self.names_files_json, self.path = load_quizzes_names(self.settings["gui"]["RRHH"]["files_quizz_out"])
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
        data, columns = create_data_for_table(self.names_files_pdf, self.names_files_json, self.path)
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
        table = Tableview(master, coldata=coldata, rowdata=data, height=10,
                          autofit=False,
                          paginated=True,
                          searchable=False)
        table.grid(row=0, column=0, sticky="nswe", padx=(5, 30))
        table.view.bind("<Double-1>", self.quizz_selected)
        return table

    def create_buttons(self, master):
        txt = ttk.ScrolledText(master, height=20, width=60, wrap=ttk.WORD)
        txt.grid(row=0, column=0, padx=5, pady=5, rowspan=3, sticky="nswe")
        create_button(master, 0, 1, text="Abrir PDF", command=self.view_pdf_action, sticky="n")
        create_button(master, 1, 1, text="Generar PDF", command=self.create_pdf_action, sticky="n", bootstyle="warning")
        create_button(master, 2, 1, text="Actualizar", command=self.update_action, sticky="n")
        return txt

    def quizz_selected(self, event):
        item = event.widget.selection()[0]
        item_data = event.widget.item(item, "values")
        self._json_file_selected = self.path + item_data[-1]
        if item_data[-1] == "No se encuentra el pdf":
            self._pdf_file_selected = None
        else:
            self._pdf_file_selected = self.path + item_data[-2]
        self.display_info_file(self._json_file_selected)

    def display_info_file(self, filepath):
        self.text_info.delete("1.0", "end")
        json_dict = json.load(open(filepath, "r"))
        for k, v in json_dict["metadata"].items():
            self.text_info.insert("end", f"{get_key_display(k)} : ", "key")
            self.text_info.insert("end", f"{v}\n", "value")
        self.text_info.tag_config("key", foreground=self.style_gui.colors.get("warning"))
        self.text_info.tag_config("value", foreground=self.style_gui.colors.get("fg"))
    
    def view_pdf_action(self):
        if os.name == 'nt':
            if self._pdf_file_selected is not None:
                # complete file
                dir_name = os.path.dirname(self._pdf_file_selected)
                os.startfile(os.path.join(dir_name, os.path.basename(self._pdf_file_selected)))
            else:
                Messagebox.show_error("No se encuentra el pdf", "Error")
        else:
            print("Not running on Windows")
    
    def create_pdf_action(self):
        if self._json_file_selected is None:
            Messagebox.show_error("No se ha seleccionado un archivo", "Error")
            return
        msg = "Esta seguro que desea crear el pdf?"
        answer = Messagebox.show_question(title="Confirmacion", message=msg)
        if answer == "No":
            return
        json_dict = json.load(open(self._json_file_selected, "r"))
        file_out = (self.path + f"{json_dict['metadata']['name_emp'].replace(' ', '')}_{json_dict['metadata']['date'].replace('/', '-')}_type_{json_dict['metadata']['type_q']}.pdf")
        tipo_op = json_dict["metadata"]["type_q"]
        generator = dict_typer_quizz_generator[tipo_op]
        generator(json_dict, None, file_out, json_dict["metadata"]["name_emp"], json_dict["metadata"]["position"],
                  "terminal", json_dict["metadata"]["admision"], json_dict["metadata"]["departure"],
                  json_dict["metadata"]["date"], json_dict["metadata"]["interviewer"])

        dir_name = os.path.dirname(self._pdf_file_selected)
        filepath = os.path.join(dir_name, os.path.basename(self._pdf_file_selected))
        Messagebox.show_info(f"PDF creado en: {filepath}", "Info")
    
    def update_action(self):
        self.names_files_pdf, self.names_files_json, self.path = load_quizzes_names(self.settings["gui"]["RRHH"]["files_quizz_out"])
        self.selectors = self.create_table_selector(self.frame_selectors)
