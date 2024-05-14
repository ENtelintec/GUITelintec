# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 13/may./2024  at 16:40 $'

import json

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.Functions_AuxFiles import load_quizzes_names
from templates.Funtions_Utils import create_label


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
        # -------------------------------variables------------------------------
        self.settings = kwargs.get('settings')
        # ------------title------------------------------
        create_label(self, 0, 0, text="Revisión de Quizzes", font=("Helvetica", 20))
        self.names_files_pdf, self.names_files_json, self.path = load_quizzes_names(self.settings["gui"]["RRHH"]["files_quizz_out"])
        
        # -------------------create widgets--------------------------------------
        frame_selectors = ttk.Frame(self)
        frame_selectors.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, padx=10, pady=10, sticky="nswe")
        self.selectors = self.create_table_selector(frame_selectors)
        self.buttons = self.create_buttons(frame_buttons)

    def create_table_selector(self, master):
        data, columns = create_data_for_table(self.names_files_pdf, self.names_files_json, self.path)
        coldata = []
        for column in columns:
            if "Fecha" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "ID" in column:
                coldata.append({"text": column, "stretch": False, "width": 50})
            else:
                coldata.append({"text": column, "stretch": True})
        table = Tableview(master, coldata=coldata, rowdata=data, height=10,
                          autofit=False,
                          paginated=True,
                          searchable=False)
        table.grid(row=0, column=0, sticky="nswe", padx=(5, 30))
        table.view.bind("<Double-1>", self.quizz_selected)

    def create_buttons(self, master):
        pass

    def quizz_selected(self, event):
        item = event.widget.selection()[0]
        item_data = event.widget.item(item, "values")
        print(item_data)