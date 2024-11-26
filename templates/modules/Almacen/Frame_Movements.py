# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 08/may./2024  at 15:14 $"

import time
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.tableview import Tableview

from static.constants import format_date, format_timestamps, log_file_db
from templates.Functions_GUI_Utils import (
    create_label,
    create_entry,
    create_Combobox,
    create_button,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.product.p_and_s_controller import (
    get_ins_db_detail,
    get_outs_db_detail,
    insert_multiple_row_movements_amc,
    udpate_multiple_row_stock_ids,
    update_movement_db,
    delete_movement_db,
    create_in_movement_db,
    create_out_movement_db,
    update_stock_db,
)
from templates.misc.Functions_Files import write_log_file
from templates.modules.Almacen.SubFrameLector import LectorScreenSelector
from templates.resources.methods.Aux_Inventory import fetch_all_products

coldata_movementes = [
    {"text": "ID Movimiento", "stretch": False},
    {"text": "ID Producto", "stretch": False},
    {"text": "SKU", "stretch": False},
    {"text": "Tipo de Movimiento", "stretch": True},
    {"text": "Cantidad", "stretch": False},
    {"text": "Fecha", "stretch": False},
    {"text": "ID SM", "stretch": True},
    {"text": "Nombre", "stretch": False},
    {"text": "UDM", "stretch": False},
    {"text": "Fabricante", "stretch": False},
    {"text": "locations", "stretch": False},
]


def end_action_db(msg, title, usernamedata):
    if msg is None or msg == "":
        return
    create_notification_permission_notGUI(
        msg, ["Administracion"], title, usernamedata["id"], 0
    )
    write_log_file(log_file_db, msg)


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


def create_new_movements(data):
    flag, error, result = insert_multiple_row_movements_amc(data)
    return flag, error, result


class MovementsFrame(ttk.Notebook):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        kwargs["coldata_moves"] = coldata_movementes
        self.frame_1 = InScreen(self, **kwargs)
        self.add(self.frame_1, text="Entradas")
        self.frame_2 = OutScreen(self, **kwargs)
        self.add(self.frame_2, text="Salidas")

    def update_procedure(self, **events):
        if "sender" in events:
            if "movements_in" == events["sender"]:
                self.frame_2.update_table(ignore_triger=True)
            elif "movements_out":
                self.frame_1.update_table(ignore_triger=True)
        else:
            self.frame_1.update_table(ignore_triger=True)
            self.frame_2.update_table(ignore_triger=True)


class InScreen(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        # variables
        self._id_product_to_modify = None
        self._old_data_movement = None
        self.table = None
        self.col_data = coldata_movementes
        self.movetement_id = None
        self.master = master
        self.columnconfigure(0, weight=1)
        self.triger_actions_callback = kwargs["triger_actions_main_callback"]
        self.usernamedata = kwargs.get("username_data", None)
        # handlers
        self._products = (
            fetch_all_products()
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
        frame_btns.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
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
        create_button(
            master,
            0,
            5,
            text="Lector",
            command=self.lector,
            style="primary",
        )

    def lector(self):
        data = {
            "data_products_gen": self._products,
            "screen": "movements_in",
            "callback_lector": self.save_data_lector,
        }
        LectorScreenSelector(self, **data)

    def save_data_lector(self, data_lector):
        msg = ""
        product_new = data_lector
        flag, error, result = create_new_movements(product_new)
        if not flag:
            msg += f"\nError al registrar movimientos: {str(error)}"
        else:
            msg += f"\nMovimientos registrados: {len(product_new)}"
            data_update_stocks = [
                [item[0], int(item[5]) + int(item[2])] for item in product_new
            ]
            flag, error, result = udpate_multiple_row_stock_ids(data_update_stocks)
            msg += (
                "\nStock actualizado"
                if flag
                else f"\nError al actualizar stock: {str(error)}"
            )
            self.update_table()
        end_action_db(msg, "Creacion de Movimientos de Entrada", self.usernamedata)

    def clear_fields(self):
        for entry in self.entries:
            if isinstance(entry, ttk.Combobox):
                entry.configure(state="normal")
                entry.set("")
                entry.configure(state="readonly")
            elif isinstance(entry, ttk.StringVar):
                entry.set("")
            elif isinstance(entry, ttk.Entry):
                entry.delete(0, "end")
        self.movetement_id = None
        self._id_product_to_modify = None
        self._old_data_movement = None
        current_date = datetime.now().strftime(format_date)
        self.entries[0].insert(0, current_date)

    def on_double_click_in_table(self, event):
        data = event.widget.item(event.widget.selection()[0])["values"]
        self.clear_fields()
        self._old_data_movement = data
        self._id_product_to_modify = data[1]
        product_name = f"{data[1]}--{data[2]}--{data[7]}"
        self.entries[2].set(product_name)
        self.movetement_id = data[0]
        self.entries[1].insert(0, data[4])
        date = datetime.strptime(data[5], format_timestamps)
        date = date.strftime(format_date)
        self.entries[0].insert(0, date)
        self.entries[3].set(f"ID Movimiento: {data[0]}")
        self.entries[4].set(f"ID Producto: {data[1]}")

    def update_table(self, ignore_triger=False):
        self._products = fetch_all_products()
        flag, error, self._ins = get_ins_db_detail()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._ins)
        if not ignore_triger:
            event = {
                "action": "update",
                "frames": ["Inventario", "Movimientos", "Inicio"],
                "sender": "movements_in",
            }
            self.triger_actions_callback(**event)

    def add_in_item(self):
        msg = ""
        id_product = self.entries[2].get().split("--")[0]
        id_movement_type = "entrada"
        quantity = self.entries[1].get()
        movement_date = self.entries[0].get()
        flag, error, lastrowid = create_in_movement_db(
            id_product, id_movement_type, quantity, movement_date, None
        )
        if not flag:
            msg += f"\nError al registrar movimiento: {id_product}"
        else:
            msg += f"\nMovimiento registrado producto {id_product}, valor de entrada {quantity}."
            new_stock = self.new_stock(int(quantity), id_product)
            flag, error, result = update_stock_db(id_product, new_stock)
            if not flag:
                msg += f"\nError al actualizar stock: {id_product}"
            else:
                msg += f"\nStock actualizado producto {id_product}."
            self.update_table()
            self.clear_fields()
        end_action_db(msg, "Creacion de Movimiento de Entrada", self.usernamedata)

    def update_in_item(self):
        if self.movetement_id is None or self._id_product_to_modify is None:
            Messagebox.show_error(
                "No se ha seleccionado un movimiento para actualizar", "Error"
            )
            return
        msg = ""
        old_quantity = self._old_data_movement[4]
        new_date = datetime.now().strftime(format_date)
        quantity = self.entries[1].get()
        flag, error, result = update_movement_db(
            self.movetement_id, quantity, new_date, None
        )
        if not flag:
            msg += f"\nError al actualizar movimiento: {self.movetement_id}--{self._id_product_to_modify}"
        else:
            msg += f"\nMovimiento actualizado producto {self._id_product_to_modify}, valor de entrada {old_quantity}-->{quantity}."
            new_stock = self.new_stock(
                int(quantity) - int(old_quantity), self._id_product_to_modify
            )
            flag, error, result = update_stock_db(self._id_product_to_modify, new_stock)
            if not flag:
                msg += f"\nError al actualizar stock: {self._id_product_to_modify}"
            else:
                msg += f"\nStock actualizado producto {self._id_product_to_modify}."
            self.update_table()
            self.clear_fields()
        end_action_db(msg, "Actualizacion de Movimiento de Entrada", self.usernamedata)

    def delete_in_item(self):
        if self.movetement_id is None:
            Messagebox.show_error("No se ha seleccionado un movimiento", "Error")
            return
        msg = ""
        quantity = self.entries[1].get()
        id_product = self.entries[2].get().split("--")[0]
        flag, error, result = delete_movement_db(self.movetement_id)
        if not flag:
            msg += f"\nError al eliminar movimiento: {self.movetement_id}--{id_product}"
        else:
            msg += f"\nMovimiento eliminado producto {id_product}, valor de movimiento {quantity}."
            new_stock = self.new_stock(-int(quantity), id_product)
            flag, error, result = update_stock_db(id_product, new_stock)
            if not flag:
                msg += f"\nError al actualizar stock: {id_product}"
            else:
                msg += f"\nStock actualizado producto {id_product}."
            self.update_table()
            self.clear_fields()
        end_action_db(msg, "Eliminacion de Movimiento de Entrada", self.usernamedata)

    def new_stock(self, value_to_add, id_product):
        for product in self._products:
            if product[0] == int(id_product):
                return product[4] + value_to_add
        return value_to_add


class OutScreen(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        # variables
        self.usernamedata = kwargs.get("username_data", None)
        self._old_data_movement = None
        self._id_product_to_modify = None
        self.table = None
        self.col_data = coldata_movementes
        self.movetement_id = None
        self.master = master
        self.columnconfigure(0, weight=1)
        # handlers
        self._products = (
            fetch_all_products()
            if "data_products_gen" not in kwargs["data"]
            else kwargs["data"]["data_products_gen"]
        )
        flag, error, self._outs = (
            get_outs_db_detail()
            if "data_movements" not in kwargs["data"]
            else (True, None, kwargs["data"]["data_movements"]["data_outs"])
        )
        self.triger_actions_callback = kwargs["triger_actions_main_callback"]
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
        create_button(
            master,
            0,
            5,
            text="Lector",
            command=self.lector,
            style="primary",
        )

    def lector(self):
        data = {
            "data_products_gen": self._products,
            "screen": "movements_out",
            "callback_lector": self.save_data_lector,
        }
        LectorScreenSelector(self, **data)

    def save_data_lector(self, data_lector):
        msg = ""
        product_new = data_lector
        flag, error, result = create_new_movements(product_new)
        if not flag:
            msg += f"\nError al registrar movimientos: {str(error)}"
        else:
            msg += f"\nMovimientos registrados: {len(product_new)}"
            data_update_stocks = [
                [item[0], int(item[5]) - int(item[2])] for item in product_new
            ]
            flag, error, result = udpate_multiple_row_stock_ids(data_update_stocks)
            msg += (
                "\nStock actualizado"
                if flag
                else f"\nError al actualizar stock: {str(error)}"
            )
            self.update_table()
        end_action_db(msg, "Creacion de Movimientos de Salida", self.usernamedata)

    def clear_fields(self):
        for entry in self.entries:
            if isinstance(entry, ttk.Combobox):
                entry.configure(state="normal")
                entry.set("")
                entry.configure(state="readonly")
            elif isinstance(entry, ttk.StringVar):
                entry.set("")
            elif isinstance(entry, ttk.Entry):
                entry.delete(0, "end")
        self.movetement_id = None
        self._id_product_to_modify = None
        self._old_data_movement = None
        current_date = datetime.now().strftime(format_date)
        self.entries[0].insert(0, current_date)

    def on_double_click_in_table(self, event):
        data = event.widget.item(event.widget.selection()[0])["values"]
        self.clear_fields()
        self._old_data_movement = data
        self._id_product_to_modify = data[1]
        product_name = f"{data[1]}--{data[2]}--{data[7]}"
        self.entries[2].set(product_name)
        self.movetement_id = data[0]
        self.entries[1].insert(0, data[4])
        date = datetime.strptime(data[5], format_timestamps)
        date = date.strftime(format_date)
        self.entries[0].insert(0, date)
        self.entries[3].set(f"ID Movimiento: {data[0]}")
        self.entries[4].set(f"ID Producto: {data[1]}")

    def update_table(self, ignore_triger=False):
        self._products = fetch_all_products()
        flag, error, self._outs = get_outs_db_detail()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._outs)
        self.table.autofit_columns()
        if not ignore_triger:
            event = {
                "action": "update",
                "frames": ["Inventario", "Movimientos", "Inicio"],
                "sender": "movements_out",
            }
            self.triger_actions_callback(**event)

    def add_out_item(self):
        msg = ""
        id_product = self.entries[2].get().split("--")[0]
        id_movement_type = "salida"
        quantity = self.entries[1].get()
        movement_date = self.entries[0].get()
        flag, error, lastrowid = create_out_movement_db(
            id_product, id_movement_type, quantity, movement_date, None
        )
        if not flag:
            msg += f"\nError al registrar movimiento para producto: {id_product}"
        else:
            msg += f"\nMovimiento registrado producto {id_product}, valor de movimiento {quantity}."
            new_stock = self.new_stock(int(quantity), id_product)
            flag, error, result = update_stock_db(id_product, new_stock)
            if not flag:
                msg += f"\nError al actualizar stock: {id_product}"
            else:
                msg += f"\nStock actualizado producto {id_product}."
            self.update_table()
            self.clear_fields()
        end_action_db(msg, "Creacion de Movimiento de Salida", self.usernamedata)

    def update_out_item(self):
        if self.movetement_id is None or self._id_product_to_modify is None:
            Messagebox.show_error("No se ha seleccionado un movimiento", "Error")
            return
        msg = ""
        new_date = datetime.now().strftime(format_date)
        quantity = self.entries[1].get()
        old_quantity = self._old_data_movement[4]
        flag, error, result = update_movement_db(
            self.movetement_id, quantity, new_date, None
        )
        if not flag:
            msg += f"\nError al actualizar movimiento: {self.movetement_id}"
        else:
            msg += f"\nMovimiento actualizado producto {self._id_product_to_modify}, valor de movimiento {old_quantity}-->{quantity}."
            new_stock = self.new_stock(
                int(quantity) - int(old_quantity), self._id_product_to_modify
            )
            flag, error, result = update_stock_db(self._id_product_to_modify, new_stock)
            if not flag:
                msg += f"\nError al actualizar stock: {self._id_product_to_modify}"
            else:
                msg += f"\nStock actualizado producto {self._id_product_to_modify}."
            self.update_table()
            self.clear_fields()
        end_action_db(msg, "Actualizacion de Movimiento de Salida", self.usernamedata)

    def delete_out_item(self):
        if self.movetement_id is None:
            Messagebox.show_error("No se ha seleccionado un movimiento", "Error")
            return
        msg = ""
        quantity = self.entries[1].get()
        id_product = self.entries[2].get().split("--")[0]
        flag, error, result = delete_movement_db(self.movetement_id)
        if not flag:
            msg += f"\nError al eliminar movimiento: {self.movetement_id}--{id_product}"
        else:
            new_stock = self.new_stock(-int(quantity), id_product)
            msg += f"\nMovimiento eliminado producto {id_product}, valor de movimiento {quantity}."
            flag, error, result = update_stock_db(id_product, new_stock)
            if not flag:
                msg += f"\nError al actualizar stock: {id_product}"
            else:
                msg += f"\nStock actualizado producto {id_product}."
            self.update_table()
            self.clear_fields()
        end_action_db(msg, "Eliminacion de Movimiento de Salida", self.usernamedata)

    def new_stock(self, value_to_add, id_product):
        for product in self._products:
            if product[0] == int(id_product):
                return product[4] + value_to_add
        return value_to_add
