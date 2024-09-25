# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 03/sept/2024  at 14:02 $"

from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from static.Models.api_contracts_models import ContractInsertForm, ContractUpdateForm
from static.extensions import format_date, format_timestamps
from templates.Functions_GUI_Utils import (
    create_label,
    create_button,
    create_date_entry,
    create_entry,
    create_Combobox,
)
from templates.controllers.contracts.contracts_controller import (
    create_contract,
    get_contract,
    update_contract,
)

import tkinter.messagebox as msgbox

import json


def split_metadata(metadata: str):
    metadata = json.loads(metadata)
    return (
        metadata["client_id"],
        metadata["contract_number"],
        metadata["identifier"],
        metadata["abbreviation"],
        metadata["location"],
        metadata["area"],
        metadata["planta"],
        metadata["emission"],
    )


def generate_columns_contract(data):
    data_out = []
    columns = [
        "id",
        "client_id",
        "number_contract",
        "identifier",
        "abbreviation",
        "emission",
        "planta",
        "area",
        "location",
        "creation",
        "quotation_id",
    ]
    for row in data:
        contract_id = row[0]
        (
            client_id,
            number_contract,
            identifier,
            abbreviation,
            planta,
            area,
            location,
            emission,
        ) = split_metadata(row[1])
        data_out.append(
            [
                contract_id,
                client_id,
                number_contract,
                identifier,
                abbreviation,
                emission,
                location,
                planta,
                area,
                row[2],
                row[3],
            ]
        )
    return data_out, columns


def create_widgets(master, data):
    create_label(
        master,
        row=0,
        column=0,
        font=("Helvetica", 12, "normal"),
        text="Emision",
        columnspan=1,
    )
    create_label(
        master, row=0, column=1, font=("Helvetica", 12, "normal"), text="Cotización ID"
    )
    create_label(
        master, row=0, column=2, font=("Helvetica", 12, "normal"), text="Planta"
    )
    create_label(master, row=0, column=3, font=("Helvetica", 12, "normal"), text="Area")
    create_label(
        master, row=2, column=0, font=("Helvetica", 12, "normal"), text="Ubicacion"
    )
    create_label(
        master, row=2, column=1, font=("Helvetica", 12, "normal"), text="Cliente ID"
    )
    create_label(
        master,
        row=2,
        column=2,
        font=("Helvetica", 12, "normal"),
        text="Numero de contrato",
    )
    create_label(
        master, row=2, column=3, font=("Helvetica", 12, "normal"), text="Identificador"
    )
    create_label(
        master, row=4, column=0, font=("Helvetica", 12, "normal"), text="Abreviatura"
    )
    # input widgets
    emission = create_date_entry(
        master, row=1, column=0, firstweekday=0, dateformat=format_date
    )
    quotation_data = data["quotations"]
    quotations_list = [f"{quotation[0]}" for quotation in quotation_data]
    quotation_code = create_Combobox(
        master,
        row=1,
        column=1,
        values=quotations_list,
    )
    planta = create_entry(
        master,
        row=1,
        column=2,
    )
    area = create_entry(
        master,
        row=1,
        column=3,
    )
    location = create_entry(
        master,
        row=3,
        column=0,
    )
    clients_data = data["clients"]
    clients_list = [f"{client[0]}-{client[1]}" for client in clients_data]
    client_id = create_Combobox(
        master,
        row=3,
        column=1,
        values=clients_list,
    )
    contract_number = create_entry(
        master,
        row=3,
        column=2,
    )
    identifier = create_entry(
        master,
        row=3,
        column=3,
    )
    abbreviation = create_entry(
        master,
        row=5,
        column=0,
    )
    return [
        emission,
        quotation_code,
        planta,
        area,
        location,
        client_id,
        contract_number,
        identifier,
        abbreviation,
    ]


class ContractsCreateFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.id_contract_edit = None
        self.columnconfigure(0, weight=1)
        self.table_contracts = None
        self.data_contracts = (
            kwargs["data"]["contracts"] if "contracts" in kwargs["data"] else []
        )
        self.data_clients = (
            kwargs["data"]["data_clients_gen"]
            if "data_clients_gen" in kwargs["data"]
            else []
        )
        self.data_quotations = (
            kwargs["data"]["quotations"] if "quotations" in kwargs["data"] else []
        )
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
        self.frame_inputs = ttk.Frame(self)
        self.frame_inputs.grid(row=1, column=0, sticky="nswe")
        self.frame_inputs.columnconfigure((0, 1, 2, 3), weight=1)
        self.entries = create_widgets(
            self.frame_inputs,
            {"clients": self.data_clients, "quotations": self.data_quotations},
        )
        # -------------------------btns---------------------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2, 3), weight=1)
        self.create_button_widgets(frame_buttons)
        # -------------------------table--------------------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=3, column=0, padx=50, pady=10, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        self.table_contracts = self.create_table(self.frame_table, True)

    def create_button_widgets(self, master):
        create_button(
            master, 0, 0, sticky="n", text="Crear", command=self.create_contract
        )
        create_button(
            master, 0, 1, sticky="n", text="Actualizar", command=self.update_contract
        )
        create_button(
            master,
            0,
            2,
            sticky="n",
            text="Cargar Contrato",
            command=self.load_contract_file,
        )
        create_button(
            master, 0, 3, sticky="n", text="Borrar", command=self.delete_contract
        )

    def create_contract(self):
        metadata = self.get_entries_values()
        validator = ContractInsertForm.from_json(
            {"metadata": metadata, "quotation_id": metadata["quotation_code"]}
        )
        if not validator.validate():
            print(validator.errors)
            return
        data = validator.data
        flag, error, result = create_contract(data["quotation_id"], data["metadata"])
        if not flag:
            msg = f"Error al crear el contrato: {error}"
            msgbox.showerror(title="Error", message=msg)
        else:
            msgbox.showinfo(
                title="Exito", message=f"Contrato creado correctamente {result}"
            )
        self.table_contracts = self.create_table(self.frame_table, True)

    def update_contract(self):
        metadata = self.get_entries_values()
        timestamp = datetime.now().strftime(format_timestamps)
        timestamps = {
            "complete": {"timestamp": None, "comment": ""},
            "update": [{"timestamp": timestamp, "comment": "update"}],
        }
        validator = ContractUpdateForm.from_json(
            {
                "id": self.id_contract_edit,
                "metadata": metadata,
                "timestamps": timestamps,
                "quotation_id": metadata["quotation_code"],
            }
        )
        if not validator.validate():
            print(validator.errors)
            return
        data = validator.data
        flag, error, result = update_contract(
            data["id"], data["metadata"], data["timestamps"]
        )
        if not flag:
            msg = f"Error al actualizar el contrato: {error}"
            msgbox.showerror(title="Error", message=msg)
        else:
            msgbox.showinfo(
                title="Exito", message=f"Contrato actualizado correctamente {result}"
            )
        self.table_contracts = self.create_table(self.frame_table, True)

    def load_contract_file(self):
        pass

    def delete_contract(self):
        pass

    def get_entries_values(self):
        values = []
        for entry in self.entries:
            if isinstance(entry, ttk.Combobox):
                values.append(entry.get())
            elif isinstance(entry, ttk.Entry):
                values.append(entry.get())
            elif isinstance(entry, ttk.DateEntry):
                values.append(entry.entry.get())
        metadata = {
            "emission": values[0],
            "quotation_code": int(values[1]),
            "planta": values[2],
            "area": values[3],
            "location": values[4],
            "client_id": int(values[5].split("-")[0]),
            "contract_number": values[6],
            "identifier": values[7],
            "abbreviation": values[8],
        }
        return metadata

    def create_table(self, master, hard_update):
        if self.table_contracts is not None:
            self.table_contracts.destroy()

        if not hard_update:
            data_rows = self.data_contracts
        else:
            flag, error, contracts = get_contract(None)
            data_rows = contracts if flag else []
        data_rows, columns = generate_columns_contract(data_rows)
        table = Tableview(
            master,
            coldata=columns,
            rowdata=data_rows,
            paginated=True,
            searchable=True,
            autofit=True,
            height=5,
            pagesize=5,
        )
        table.grid(row=0, column=0, padx=10, pady=5, sticky="n")
        table.view.bind("<Double-1>", self.on_double_click_table)
        return table

    def on_double_click_table(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self.id_contract_edit = int(row[0])
        (
            emission,
            quotation_code,
            planta,
            area,
            location,
            client_id,
            contract_number,
            identifier,
            abbreviation,
        ) = (
            row[5],
            row[10],
            row[6],
            row[7],
            row[8],
            row[1],
            row[2],
            row[3],
            row[4],
        )
        self.set_values_entries(
            (
                emission,
                quotation_code,
                planta,
                area,
                location,
                client_id,
                contract_number,
                identifier,
                abbreviation,
            )
        )

    def set_values_entries(self, data):
        for index, item in enumerate(self.entries):
            if isinstance(item, ttk.Combobox):
                if index >= 2:
                    for index_c in self.data_clients:
                        if str(index_c[0]) == data[index]:
                            value = f"{index_c[0]}-{index_c[1]}"
                            item.set(value)
                            break
                else:
                    item.set(data[index])
            elif isinstance(item, ttk.Entry):
                item.delete(0, "end")
                item.insert(0, data[index])
            elif isinstance(item, ttk.DateEntry):
                self.entries[index].destroy()
                self.entries[index] = create_date_entry(
                    self.frame_inputs,
                    firstweekday=0,
                    dateformat=format_date,
                    startdate=datetime.strptime(data[index], format_date),
                    row=1,
                    column=0,
                )
