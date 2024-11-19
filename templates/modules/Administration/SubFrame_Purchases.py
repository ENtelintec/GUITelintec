# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/nov/2024  at 10:58 $"

from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.tableview import Tableview

from static.Models.api_purchases_models import PurchasePostForm
from static.constants import format_date, format_timestamps
from templates.Functions_GUI_Utils import (
    create_label,
    create_entry,
    create_Combobox,
    create_button,
    create_date_entry,
)
from templates.controllers.product.p_and_s_controller import get_all_suppliers
from templates.controllers.purchases.purchases_admin_controller import (
    insert_new_purchase_db,
)
from templates.resources.midleware.Functions_midleware_admin import (
    get_data_table_purchases,
)


def create_input_widgets(master, data):
    create_label(master, text="ID: ", row=0, column=0, sticky="w")
    create_label(master, text="Nombre: ", row=1, column=0, sticky="w")
    create_label(master, text="Cantidad: ", row=2, column=0, sticky="w")
    create_label(master, text="Proveedor: ", row=3, column=0, sticky="w")
    create_label(master, text="Enlace: ", row=4, column=0, sticky="w")
    create_label(master, text="Comentario: ", row=5, column=0, sticky="w")
    create_label(master, text="Fecha requerida: ", row=6, column=0, sticky="w")
    # inputs
    svar_id = ttk.StringVar(value="")
    create_label(master, textvariable=svar_id, row=0, column=1, sticky="w")
    name = create_entry(master, row=1, column=1)
    quantity = create_entry(master, row=2, column=1)
    data_providers = [item[1] for item in data["providers"]]
    provider = create_Combobox(
        master, row=3, column=1, values=data_providers, state="normal"
    )
    link = create_entry(master, row=4, column=1)
    comment = create_entry(master, row=5, column=1)
    date = create_date_entry(
        master, row=6, column=1, firstweekday=0, dateformat=format_date
    )
    return svar_id, name, quantity, provider, link, comment, date


def create_btns(master, callbacks):
    create_button(
        master,
        row=0,
        column=0,
        text="Agregar solicitud",
        command=callbacks["add"],
        style="success",
    )
    create_button(
        master,
        row=0,
        column=1,
        text="Actualizar solicitud",
        command=callbacks["update"],
        style="info",
    )
    create_button(
        master,
        row=0,
        column=2,
        text="Eliminar",
        command=callbacks["delete"],
        style="danger",
    )
    create_button(
        master,
        row=1,
        column=0,
        text="Limpiar",
        command=callbacks["clear"],
        style="warning",
    )
    create_button(
        master,
        row=1,
        column=1,
        text="Actualizar tabla",
        command=callbacks["update_table"],
        style="info",
    )


def create_table(master, coldata, row_data, callback):
    table = Tableview(
        master,
        coldata=coldata,
        autofit=True,
        paginated=True,
        searchable=True,
        rowdata=row_data,
        height=15,
    )
    table.grid(row=1, column=0, sticky="nswe", padx=(5, 30))
    table.view.bind("<Double-1>", callback)
    columns_header = table.get_columns()
    for item in columns_header:
        if item.headertext in ["Completado", "Actualizado"]:
            item.hide()
    return table


def update_table(table):
    data = fetch_purchases_db()
    row_data, coldata = (data.get("data", []), data.get("columns", []))
    if len(row_data) == 0 or len(coldata) == 0 or len(row_data[0]) != len(coldata):
        print("No hay datos para actualizar. Error....")
        return None
    table.unload_table_data()
    table.build_table_data(coldata, row_data)
    columns_header = table.get_columns()
    for item in columns_header:
        if item.headertext in ["Completado", "Actualizado"]:
            item.hide()


def get_entries_values(entries):
    values = []
    for entry in entries:
        if isinstance(entry, ttk.Combobox):
            values.append(entry.get())
        elif isinstance(entry, ttk.StringVar):
            values.append(entry.get())
        elif isinstance(entry, ttk.DateEntry):
            values.append(entry.entry.get())
        elif isinstance(entry, ttk.Entry):
            values.append(entry.get())
        else:
            values.append(None)
    return values


def set_values_entries(entries, values):
    for index, entry in enumerate(entries):
        if isinstance(entry, ttk.Combobox):
            entry.set(values[index])
        elif isinstance(entry, ttk.StringVar):
            entry.set(values[index])
        elif isinstance(entry, ttk.DateEntry):
            entry.entry.delete(0, "end")
            entry.entry.insert(0, values[index])
        elif isinstance(entry, ttk.Entry):
            entry.delete(0, "end")
            entry.insert(0, values[index])


def fetch_purchases_db():
    data, code = get_data_table_purchases({"limit_min": 0, "limit_max": 100})
    return data


def fetch_providers_db():
    flag, error, providers = get_all_suppliers()
    return providers


class RequestPurchaseFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.data_providers = kwargs["data"].get(
            "data_providers_gen", fetch_providers_db()
        )
        self.id_petition_modify = None
        self.data_purchases = kwargs["data"].get(
            "data_purchases_admin", fetch_purchases_db()
        )
        # ---------------------------------Title-------------------------------------------------
        create_label(
            self,
            text="Compras",
            font=("Arial", 20),
            row=0,
            column=0,
            sticky="w",
        )
        # ---------------------------------Inputs-------------------------------------------------
        self.frame_inputs = ttk.Frame(self)
        self.frame_inputs.grid(row=1, column=0, sticky="nswe")
        self.frame_inputs.columnconfigure((0, 1), weight=1)
        self.entries = create_input_widgets(
            self.frame_inputs, {"providers": self.data_providers}
        )
        # ---------------------------------Btns-------------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=2, column=0, sticky="nswe")
        frame_btns.columnconfigure((0, 1, 2), weight=1)
        callbacks = {
            "add": self.add_petition,
            "update": self.update_petition,
            "delete": self.delete_petition,
            "clear": self.clear_entries,
            "update_table": lambda: update_table(self.table),
        }
        create_btns(frame_btns, callbacks)
        # ---------------------------------Table-------------------------------------------------
        frame_table = ttk.Frame(self)
        frame_table.grid(row=3, column=0, sticky="nswe")
        frame_table.columnconfigure(0, weight=1)
        self.table = create_table(
            frame_table,
            self.data_purchases.get("columns", []),
            self.data_purchases.get("data", []),
            self.on_doble_click_table,
        )

    def clear_entries(self):
        self.entries = list(self.entries)
        for index, entry in enumerate(self.entries):
            if isinstance(entry, ttk.Combobox):
                entry.set("")
            elif isinstance(entry, ttk.StringVar):
                entry.set("")
            elif isinstance(entry, ttk.DateEntry):
                self.entries[index].destroy()
                self.entries[index] = create_date_entry(
                    self.frame_inputs,
                    firstweekday=0,
                    dateformat=format_date,
                    startdate=datetime.now(),
                    row=5,
                    column=1,
                )
            elif isinstance(entry, ttk.Entry):
                entry.delete(0, "end")
        self.entries = tuple(self.entries)
        self.id_petition_modify = None

    def on_doble_click_table(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        print(row)
        self.clear_entries()
        self.id_petition_modify = int(row[0])
        set_values_entries(self.entries, row)

    def add_petition(self):
        values = get_entries_values(self.entries)
        if values[1] == "" or values[2] == "" or values[3] == "":
            Messagebox.show_error(
                "No se puede agregar una solicitud sin nombre o cantidad", "Error"
            )
            return
        timestamp_now = datetime.now().strftime(format_timestamps)
        data_dict = {
            "metadata": {
                "name": values[1],
                "quantity": values[2],
                "supplier": values[3],
                "link": values[4],
                "comments": values[5],
                "date_required": values[6],
            },
            "creation": timestamp_now,
        }
        validator = PurchasePostForm.from_json(data_dict)
        if not validator.validate():
            print(data_dict)
            print(validator.errors)
            return
        data = validator.data
        flag, error, result = insert_new_purchase_db(data["metadata"], data["creation"])
        print(flag, error, result)

    def update_petition(self):
        pass

    def delete_petition(self):
        pass
