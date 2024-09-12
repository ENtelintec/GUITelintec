# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/jul./2024  at 17:14 $"

from tkinter.filedialog import askopenfilename

import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.Functions_GUI_Utils import create_label, create_Combobox, create_button
from templates.resources.methods.Functions_Aux_Admin import (
    read_file_tenium_contract,
)

import json


def procces_quotation_list(data):
    quotations = []
    for item in data:
        metadata = json.loads(item[1])
        quotations.append(
            [
                item[0],
                metadata["company"],
                metadata["quotation_code"],
                metadata["codigo"],
                item[3],
            ]
        )
    return quotations


def create_widgets(master, data):
    create_label(
        master, row=0, column=0, text="Cotización", font=("Helvetica", 12, "normal")
    )
    quotations_list = procces_quotation_list(data)
    cotization_selector = create_Combobox(
        master, row=0, column=1, values=quotations_list
    )
    cotization_selector.set("")
    return [cotization_selector]


def compare_vectors_quotation_contract(vector1, vector2):
    # coldata_c = ["Partida","Descripción","Cantidad","Unidad","Precio Unitario","Total","Tipo","Marca","Nro. Parte","Descripción Larga",
    #              " ", "Partida", "Descripción", "Cantidad", "Unidad", "Precio Unitario", "Importe"]
    # out = vector1 + ["<-->"] + vector2
    out = [
        vector2[6],
        vector2[11],
        vector2[7],
        vector2[1],
        vector2[9],
        round(vector2[9] * vector2[7], 2),
        vector2[3],
        vector2[2],
        vector2[5],
        vector2[10],
        "<-->",
        vector1[0],
        vector1[1],
        vector1[2],
        vector1[3],
        vector1[4],
        vector1[5],
    ]
    flag = False
    if (
        round(vector2[9], 2) - 0.01 <= vector1[4] <= round(vector2[9], 2) + 0.01
    ):  # company
        flag = True
    return flag, out


class ContractsDocsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.id_quotation_selected = None
        self.products_contract = None
        self.columnconfigure(0, weight=1)
        self.data_quotations = (
            kwargs["data"]["quotations"] if "quotations" in kwargs["data"] else []
        )
        self.data_quotation = None
        self.table_comparision = None
        # ---------------------------title-------------------------------------
        create_label(
            self,
            row=0,
            column=0,
            text="Crear contrato",
            font=("Helvetica", 30, "bold"),
            columnspan=1,
        )
        # -------------------------inputs--------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure((0, 1), weight=1)
        self.entries = create_widgets(frame_inputs, self.data_quotations)
        quotation_selector = self.entries[0]
        quotation_selector.bind("<<ComboboxSelected>>", self.on_quotation_selected)
        # -------------------------btns---------------------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2), weight=1)
        self.create_button_widgets(frame_buttons)
        # -------------------------displayProducts-----------------------------
        self.frame_display_p = ttk.Frame(self)
        self.frame_display_p.grid(row=3, column=0, sticky="nswe")
        self.frame_display_p.columnconfigure(0, weight=1)
        self.display_outputs = self.create_display_widgets()

    def create_button_widgets(self, master):
        create_button(
            master,
            0,
            0,
            sticky="n",
            text="Cargar Contrato",
            command=self.load_contract_file,
            bootstyle="primary",
        )
        create_button(
            master,
            0,
            1,
            sticky="n",
            text="Comparar",
            command=self.compare_doc_quotation,
            bootstyle="secondary",
        )
        create_button(
            master,
            0,
            2,
            sticky="n",
            text="Crear registro",
            command=self.create_contract,
            bootstyle="success",
        )

    def load_contract_file(self):
        filepath = askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filepath:
            print(f"Selected file: {filepath}")
            pattern_items = "_______________________________ _______________________________ _______________________________ _________"
            phrase = "contiene los siguientes servicios:"
            self.products_contract = read_file_tenium_contract(
                filepath, pattern_items, phrase
            )
        else:
            self.products_contract = None
            print("No file selected")

    def compare_doc_quotation(self):
        if self.products_contract is None or self.data_quotation is None:
            print("No hay datos para comparar")
            return
        products_quotation = json.loads(self.data_quotation[2])
        table_rows = []
        flags = []
        if len(self.products_contract) >= len(products_quotation):
            df = pd.DataFrame.from_records(products_quotation)
            for index, item1 in enumerate(self.products_contract):
                partida_1 = int(item1["partida"])
                item2 = df.loc[df["partida"] == partida_1].values.tolist()
                item2 = (
                    item2[0]
                    if item2
                    else [None, "", "", "", "", "", 0, 0, False, 0.0, "", ""]
                )
                flag, result = compare_vectors_quotation_contract(
                    list(item1.values()), item2
                )
                table_rows.append(result)
                flags.append(flag)
            self.table_comparision = self.create_display_widgets(table_rows, flags)
        else:
            df = pd.DataFrame.from_records(self.products_contract)
        # self.table_comparision = self.create_display_widgets()

    def create_display_widgets(self, rowdata=None, flags=None):
        rowdata = rowdata if rowdata is not None else []
        master = self.frame_display_p
        if self.table_comparision is not None:
            self.table_comparision.destroy()
        create_label(
            master,
            row=0,
            column=0,
            text="Productos Cotizacion y Contrato",
            font=("Helvetica", 12, "normal"),
            columnspan=1,
        )
        # entry
        coldata_c = [
            {"text": "Partida", "stretch": False, "width": 85},
            {"text": "Descripción", "stretch": False, "width": 150},
            {"text": "Cantidad", "stretch": False, "width": 55},
            {"text": "Unidad", "stretch": False, "width": 55},
            {"text": "Precio Unitario", "stretch": False, "width": 85},
            {"text": "Total", "stretch": False, "width": 85},
            {"text": "Tipo", "stretch": False, "width": 110},
            {"text": "Marca", "stretch": False, "width": 110},
            {"text": "Nro. Parte", "stretch": False, "width": 85},
            {"text": "Descripción Larga", "stretch": False, "width": 150},
            {"text": " ", "stretch": False, "width": 25},
            {"text": "Partida", "stretch": False, "width": 85},
            {"text": "Descripción", "stretch": False, "width": 150},
            {"text": "Cantidad", "stretch": False, "width": 55},
            {"text": "Unidad", "stretch": False, "width": 55},
            {"text": "Precio Unitario", "stretch": False, "width": 85},
            {"text": "Importe", "stretch": False, "width": 25},
        ]
        tpc = Tableview(
            master,
            coldata=coldata_c,
            rowdata=rowdata,
            paginated=False,
            searchable=True,
            bootstyle="primary",
            height=20,
        )
        tpc.grid(row=1, column=0, sticky="we")
        tpc.view.tag_configure(
            "complete", font=("Arial", 10, "normal"), background="white"
        )
        tpc.view.tag_configure(
            "incomplete", font=("Arial", 11, "bold"), background="#98F5FF"
        )
        items_t = tpc.view.get_children()
        for index, item_t in enumerate(items_t):
            if flags[index]:
                # print(index, flags[index])
                tpc.view.item(item_t, tags="complete")
            else:
                tpc.view.item(item_t, tags="incomplete")
        return tpc

    def create_contract(self):
        if self.id_quotation_selected:
            print(self.id_quotation_selected)

    def on_quotation_selected(self, event):
        value = event.widget.get()  # Get the selected value
        if value:
            try:
                self.id_quotation_selected = int(value.split(" ")[0])
                for quotation in self.data_quotations:
                    if int(quotation[0]) == self.id_quotation_selected:
                        self.data_quotation = quotation
                        print("quotation selected: ", self.id_quotation_selected)
            except ValueError:
                self.id_quotation_selected = None
