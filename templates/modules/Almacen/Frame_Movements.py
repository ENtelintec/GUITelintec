# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/may./2024  at 15:14 $"

import time
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from static.extensions import format_date, format_timestamps
from templates.Functions_GUI_Utils import (
    create_label,
    create_entry,
    create_Combobox,
    create_button,
)
from templates.controllers.index import DataHandler
from templates.controllers.product.p_and_s_controller import (
    get_ins_db_detail,
    get_outs_db_detail,
)

coldata_movementes = [
    {"text": "ID Movimiento", "stretch": False},
    {"text": "ID Producto", "stretch": False},
    {"text": "SKU", "stretch": False},
    {"text": "Tipo de Movimiento", "stretch": True},
    {"text": "Cantidad", "stretch": False},
    {"text": "Fecha", "stretch": False},
    {"text": "ID SM", "stretch": True},
    {"text": "Nombre", "stretch": False},
]


def create_movement_widgets(master, values_products):
    entries = []
    master.columnconfigure((0, 1, 2, 3, 4), weight=1)
    # Inputs left
    create_label(master, 0, 0, text="Fecha de entrega", sticky="w")
    date_delivered = create_entry(master, row=0, column=1)
    date_delivered.insert(0, datetime.now().strftime(format_date))
    entries.append(date_delivered)
    create_label(master, 1, 0, text="Cantidad", sticky="w")
    input_quantity = create_entry(master, row=1, column=1)
    entries.append(input_quantity)
    create_label(master, 2, 0, text="Producto", sticky="w")
    supp_selector = create_Combobox(master, values=values_products, row=2, column=1)
    entries.append(supp_selector)
    _svar_id_move_info = ttk.StringVar(value="")
    create_label(master, 3, 0, textvariable=_svar_id_move_info, sticky="n")
    entries.append(_svar_id_move_info)
    _svar_id_product_info = ttk.StringVar(value="")
    create_label(master, 3, 1, textvariable=_svar_id_product_info, sticky="n")
    entries.append(_svar_id_product_info)
    _svar_sku_info = ttk.StringVar(value="")
    create_label(master, 3, 2, textvariable=_svar_sku_info, sticky="n")
    entries.append(_svar_sku_info)
    return entries


class MovementsFrame(ttk.Notebook):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        kwargs["coldata_moves"] = coldata_movementes
        frame_1 = InScreen(self, **kwargs)
        self.add(frame_1, text="Entradas")
        frame_2 = OutScreen(self, **kwargs)
        self.add(frame_2, text="Salidas")


class InScreen(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        # variables
        self._id_product_to_modify = None
        self._old_data_movement = None
        self.table = None
        self.col_data = coldata_movementes
        self.movetement_id = None
        self.master = master
        self.columnconfigure(0, weight=1)
        # handlers
        self._data = DataHandler()
        self._products = (
            self._data.get_all_products()
            if "data_products_gen" not in kwargs["data"]
            else kwargs["data"]["data_products_gen"]
        )
        flag, error, self._ins = (
            get_ins_db_detail()
            if "data_movements" not in kwargs["data"]
            else (True, None, kwargs["data"]["data_movements"]["data_ins"])
        )
        # -------------------------------Title----------------------------------------------
        create_label(self, 0, 0, text="Entradas", font=("Helvetica", 22, "bold"))
        # -------------------------------Table-------------------------------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=0, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        ttk.Label(self.frame_table, text="Tabla de Entradas", font=("Arial", 20)).grid(
            row=0, column=0, sticky="w", padx=5, pady=10
        )
        self.create_table(self.frame_table)
        # -------------------------------inputs-------------------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=2, column=0, sticky="nswe")
        frame_inputs.columnconfigure((0, 1), weight=1)
        values_products = [
            f"{product[0]}--{product[1]}--{product[2]}" for product in self._products
        ]
        self.entries = create_movement_widgets(frame_inputs, values_products)
        # --------------------------------btns-------------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=3, column=0, sticky="nswe")
        frame_btns.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.create_buttons(frame_btns)

    def create_table(self, master):
        if self.table is not None:
            self.table.destroy()
        self.table = Tableview(
            master,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True,
            coldata=self.col_data,
            rowdata=self._ins,
        )
        self.table.grid(row=1, column=0, sticky="nswe", padx=15, pady=5)
        self.table.view.bind("<Double-1>", self.on_double_click_in_table)

    def create_buttons(self, master):
        """Creates the buttons of the Inputs screen, includes the buttons to add, update and delete inputs"""
        create_button(
            master,
            0,
            0,
            text="Agregar Entrada",
            command=self.add_in_item,
            style="primary",
        )
        create_button(
            master,
            0,
            1,
            text="Actualizar Entrada",
            command=self.update_in_item,
            style="primary",
        )
        create_button(
            master,
            0,
            2,
            text="Eliminar Entrada",
            command=self.delete_in_item,
            style="warning",
        )
        create_button(
            master,
            0,
            3,
            text="Limpiar Campos",
            command=self.clear_fields,
            style="primary",
        )
        create_button(
            master,
            0,
            4,
            text="Actualizar Tabla",
            command=self.update_table,
            style="primary",
        )

    def clear_fields(self):
        for entry in self.entries:
            if isinstance(entry, ttk.Entry):
                entry.delete(0, "end")
            elif isinstance(entry, ttk.Combobox):
                entry.set("")
            elif isinstance(entry, ttk.StringVar):
                entry.set("")
        self.movetement_id = None
        self._id_product_to_modify = None
        self._old_data_movement = None

    def on_double_click_in_table(self, event):
        data = self.table.view.item(self.table.view.focus())["values"]
        self.clear_fields()
        self._old_data_movement = data
        self._id_product_to_modify = data[1]
        product_name = f"{data[1]}--{data[2]}--{data[3]}"
        self.entries[2].set(product_name)
        self.movetement_id = data[0]
        self.entries[1].insert(0, data[4])
        date = datetime.strptime(data[5], format_timestamps)
        date = date.strftime(format_date)
        self.entries[0].insert(0, date)
        self.entries[3].set(f"ID Movimiento: {data[0]}")
        self.entries[4].set(f"ID Producto: {data[1]}")

    def update_table(self):
        flag, error, self._ins = get_ins_db_detail()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._ins)
        self.table.autofit_columns()

    def update_in_item(self):
        if self.movetement_id is None or self._id_product_to_modify is None:
            return
        old_quantity = self._old_data_movement[4]
        new_date = datetime.now().strftime(format_date)
        quantity = self.entries[1].get()
        self._data.update_in_movement(self.movetement_id, quantity, new_date, None)
        new_stock = self.new_stock(
            int(quantity) - int(old_quantity), self._id_product_to_modify
        )
        self._data.update_stock(self._id_product_to_modify, new_stock)
        self.update_table()
        self.clear_fields()
        current_date = datetime.now().strftime(format_date)
        self.entries[0].insert(0, current_date)

    def add_in_item(self):
        id_product = self.entries[2].get().split("--")[0]
        id_movement_type = "entrada"
        quantity = self.entries[1].get()
        movement_date = self.entries[0].get()
        self._data.create_in_movement(
            id_product, id_movement_type, quantity, movement_date, None
        )
        new_stock = self.new_stock(int(quantity), id_product)
        self._data.update_stock(id_product, new_stock)
        self.update_table()
        self.clear_fields()
        current_date = datetime.now().strftime(format_date)
        self.entries[0].insert(0, current_date)

    def new_stock(self, value_to_add, id_product):
        for product in self._products:
            if product[0] == int(id_product):
                return product[4] + value_to_add
        return value_to_add

    def delete_in_item(self):
        if self.movetement_id is None:
            return
        self._data.delete_in_movement(self.movetement_id)
        quantity = self.entries[1].get()
        id_product = self.entries[2].get().split("--")[0]
        new_stock = self.new_stock(-int(quantity), id_product)
        self._data.update_stock(id_product, new_stock)
        self.update_table()
        self.clear_fields()
        current_date = datetime.now().strftime(format_date)
        self.entries[0].insert(0, current_date)


class OutScreen(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        # variables
        self._old_data_movement = None
        self._id_product_to_modify = None
        self.table = None
        self.col_data = coldata_movementes
        self.movetement_id = None
        self.master = master
        self.columnconfigure(0, weight=1)
        # handlers
        self._data = DataHandler()
        self._products = (
            self._data.get_all_products()
            if "data_products_gen" not in kwargs["data"]
            else kwargs["data"]["data_products_gen"]
        )
        flag, error, self._outs = (
            get_outs_db_detail()
            if "data_movements" not in kwargs["data"]
            else (True, None, kwargs["data"]["data_movements"]["data_outs"])
        )
        # -------------------------------Title----------------------------------------------
        create_label(self, 0, 0, text="Salidas", font=("Helvetica", 22, "bold"))
        # -------------------------------Table-------------------------------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=0, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        ttk.Label(self.frame_table, text="Tabla de Salidas", font=("Arial", 20)).grid(
            row=0, column=0, sticky="w", padx=5, pady=10
        )
        self.create_table(self.frame_table)
        # -------------------------------inputs-------------------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=2, column=0, sticky="nswe")
        frame_inputs.columnconfigure((0, 1), weight=1)
        values_products = [
            f"{product[0]}--{product[1]}--{product[2]}" for product in self._products
        ]
        self.entries = create_movement_widgets(frame_inputs, values_products)
        # --------------------------------btns-------------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=3, column=0, sticky="nswe")
        frame_btns.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.create_buttons(frame_btns)

    def create_table(self, master):
        if self.table is not None:
            self.table.destroy()
        self.table = Tableview(
            master,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True,
            coldata=self.col_data,
            rowdata=self._outs,
        )
        self.table.grid(row=1, column=0, sticky="nswe", padx=15, pady=5)
        self.table.view.bind("<Double-1>", self.on_double_click_in_table)

    def create_buttons(self, master):
        """Creates the buttons of the Inputs screen, includes the buttons to add, update and delete inputs"""
        create_button(
            master,
            0,
            0,
            text="Agregar Salida",
            command=self.add_out_item,
            style="primary",
        )
        create_button(
            master,
            0,
            1,
            text="Actualizar Salida",
            command=self.update_out_item,
            style="primary",
        )
        create_button(
            master,
            0,
            2,
            text="Eliminar Salida",
            command=self.delete_out_item,
            style="warning",
        )
        create_button(
            master,
            0,
            3,
            text="Limpiar Campos",
            command=self.clear_fields,
            style="primary",
        )
        create_button(
            master,
            0,
            4,
            text="Actualizar Tabla",
            command=self.update_table,
            style="primary",
        )

    def clear_fields(self):
        for entry in self.entries:
            if isinstance(entry, ttk.Entry):
                entry.delete(0, "end")
            elif isinstance(entry, ttk.Combobox):
                entry.set("")
            elif isinstance(entry, ttk.StringVar):
                entry.set("")
        self.movetement_id = None
        self._id_product_to_modify = None
        self._old_data_movement = None

    def on_double_click_in_table(self, event):
        data = self.table.view.item(self.table.view.focus())["values"]
        self.clear_fields()
        self._old_data_movement = data
        self._id_product_to_modify = data[1]
        product_name = f"{data[1]}--{data[2]}--{data[3]}"
        self.entries[2].set(product_name)
        self.movetement_id = data[0]
        self.entries[1].insert(0, data[4])
        date = datetime.strptime(data[5], format_timestamps)
        date = date.strftime(format_date)
        self.entries[0].insert(0, date)
        self.entries[3].set(f"ID Movimiento: {data[0]}")
        self.entries[4].set(f"ID Producto: {data[1]}")

    def update_table(self):
        flag, error, self._outs = get_outs_db_detail()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._outs)
        self.table.autofit_columns()

    def update_out_item(self):
        if self.movetement_id is None or self._id_product_to_modify is None:
            return
        new_date = datetime.now().strftime(format_date)
        quantity = self.entries[1].get()
        old_quantity = self._old_data_movement[4]
        self._data.update_out_movement(self.movetement_id, quantity, new_date, None)
        new_stock = self.new_stock(
            int(quantity) - int(old_quantity), self._id_product_to_modify
        )
        self._data.update_stock(self._id_product_to_modify, new_stock)
        self.update_table()
        self.clear_fields()
        current_date = datetime.now().strftime(format_date)
        self.entries[0].insert(0, current_date)

    def add_out_item(self):
        id_product = self.entries[2].get().split("--")[0]
        id_movement_type = "salida"
        quantity = self.entries[1].get()
        movement_date = self.entries[0].get()
        self._data.create_out_movement(
            id_product, id_movement_type, quantity, movement_date, None
        )
        new_stock = self.new_stock(int(quantity), id_product)
        self._data.update_stock(id_product, new_stock)
        self.update_table()
        self.clear_fields()
        current_date = datetime.now().strftime(format_date)
        self.entries[0].insert(0, current_date)

    def new_stock(self, value_to_add, id_product):
        for product in self._products:
            if product[0] == int(id_product):
                return product[4] + value_to_add
        return value_to_add

    def delete_out_item(self):
        if self.movetement_id is None:
            return
        self._data.delete_out_movement(self.movetement_id)
        quantity = self.entries[1].get()
        id_product = self.entries[2].get().split("--")[0]
        new_stock = self.new_stock(-int(quantity), id_product)
        self._data.update_stock(id_product, new_stock)
        self.update_table()
        self.clear_fields()
        current_date = datetime.now().strftime(format_date)
        self.entries[0].insert(0, current_date)
