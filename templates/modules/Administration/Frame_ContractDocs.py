# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/jul./2024  at 17:14 $'

from tkinter.filedialog import askopenfilename

import ttkbootstrap as ttk

from static.extensions import path_contract_files
from templates.Functions_Utils import create_label, create_Combobox, create_button
from templates.resources.methods.Functions_Aux_Admin import get_filenames_contracts

import json


def procces_quotation_list(data):
    quotations = []
    for item in data:
        metadata = json.loads(item[1])
        quotations.append([item[0], metadata["company"], metadata["quotation_code"], metadata["codigo"], item[3]])
    return quotations


def create_widgets(master, data):
    contract_list = ["cargar..."] + get_filenames_contracts()
    contract_selector = create_Combobox(master, row=0, column=0, values=contract_list)
    contract_selector.set("")
    quotations_list = procces_quotation_list(data)
    cotization_selector = create_Combobox(master, row=0, column=1, values=quotations_list)
    cotization_selector.set("")
    return [contract_selector, cotization_selector]


def load_contract_file():
    filename = askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if filename:
        print(f"Selected file: {filename}")
        # move file to directory
        with open(filename, "rb") as file:
            data = file.read()
        # save file in directory
        just_name = filename.split("/")[-1]
        with open(path_contract_files+"/"+just_name, "wb") as file:
            file.write(data)
        print(f"File saved successfully: {path_contract_files+'/'+just_name}")
    else:
        print("No file selected")


class ContractsDocsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.data_quotations = kwargs["data"]["quotations"] if "quotations" in kwargs["data"] else []
        # ---------------------------title-------------------------------------
        create_label(self, row=0, column=0, text="Crear contrato", font=("Helvetica", 30, "bold"), columnspan=1)
        # -------------------------inputs--------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        self.entries = create_widgets(frame_inputs, self.data_quotations)
        # -------------------------btns---------------------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, sticky="nswe")
        self.create_button_widgets(frame_buttons)

    def create_button_widgets(self, master):
        create_button(master, 0, 0, text="Crear", command=self.compare_doc_quotation)
        create_button(master, 0, 1, text="Cargar Contrato", command=load_contract_file)

    def compare_doc_quotation(self):
        pass
