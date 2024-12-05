# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 05/dic/2024  at 11:19 $"

from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from static.constants import format_timestamps
from templates.Functions_GUI_Utils import (
    create_label,
    create_button,
    create_Combobox,
    create_entry,
)
from templates.resources.methods.Aux_Inventory import (
    fetch_all_products,
    fetch_all_movements,
    coldata_movements,
    columns_movements_widgets_lector,
    coldata_inventory,
)


class MultipleMovementsScreen(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        # variables
        self.entries = None
        self.data_new_movements = []
        self.table = None
        self.table_moves = None
        self.col_data_moves = coldata_movements
        self.col_data_products = coldata_inventory
        self.columns = columns_movements_widgets_lector
        # handlers
        self.triger_actions_callback = kwargs["triger_actions_main_callback"]
        self._products = (
            fetch_all_products()
            if "data_products_gen" not in kwargs["data"]
            else kwargs["data"]["data_products_gen"]
        )
        self._movements = (
            fetch_all_movements()
            if "data_movements" not in kwargs["data"]
            else kwargs["data"]["data_movements"]["data_all"]
        )
        # -------------------------------Title----------------------------------------------
        create_label(
            self, 0, 0, text="Movimientos Multiples", font=("Helvetica", 22, "bold")
        )
        # -------------------------------Table Products-------------------------------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=0, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        ttk.Label(self.frame_table, text="Tabla de productos", font=("Arial", 20)).grid(
            row=0, column=0, sticky="w", padx=5, pady=10
        )
        self.create_table(self.frame_table)
        # -------------------------------inputs-------------------------------------------------
        self.frame_products = ttk.Frame(self)
        self.frame_products.grid(row=2, column=0, sticky="nswe")
        self.frame_products.columnconfigure(0, weight=1)
        self.create_entries_widgets(self.frame_products)
        # --------------------------------btns-------------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=3, column=0, sticky="nswe")
        frame_btns.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.create_buttons(frame_btns)
        # -------------------------------Table Movements-------------------------------------------------
        self.frame_table_moves = ttk.Frame(self)
        self.frame_table_moves.grid(row=4, column=0, sticky="nswe")
        self.frame_table_moves.columnconfigure(0, weight=1)
        ttk.Label(
            self.frame_table_moves, text="Tabla de movimientos", font=("Arial", 20)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)
        self.create_table_movements(self.frame_table_moves)

    def create_buttons(self, master):
        """Creates the buttons of the Inputs screen, includes the buttons to add, update and delete inputs"""
        create_button(
            master,
            0,
            0,
            text="Agregar Movimientos",
            command=self.add_movements,
            style="success",
        )
        create_button(
            master,
            0,
            1,
            text="Actualizar Movimientos",
            command=self.update_movements,
            style="info",
        )

    def create_table(self, master):
        if self.table is not None:
            self.table.destroy()
        self.table = Tableview(
            master,
            bootstyle="primary",
            paginated=True,
            pagesize=5,
            height=5,
            searchable=True,
            autofit=True,
            coldata=self.col_data_products,
            rowdata=self._products,
        )
        self.table.grid(row=1, column=0, sticky="nswe", padx=15, pady=5)
        self.table.view.bind("<Double-1>", self.on_double_click_in_table)

    def on_double_click_in_table(self, event):
        row_data = event.widget.item(event.widget.selection()[0])["values"]
        id_selected = int(row_data[0])
        list_ids = [item[0] for item in self.data_new_movements]
        datetime_now = datetime.now().strftime(format_timestamps)
        if id_selected in list_ids:
            new_products = [
                item for item in self.data_new_movements if item[0] != id_selected
            ]
            self.data_new_movements = new_products
        else:
            self.data_new_movements.append(
                [id_selected, row_data[2], None, 0, datetime_now, None, row_data[4], ""]
            )
        self.recreate_entry()

    def create_table_movements(self, master):
        if self.table_moves is not None:
            self.table_moves.destroy()
        self.table_moves = Tableview(
            master,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True,
            coldata=self.col_data_moves,
            rowdata=self._movements,
        )
        self.table_moves.grid(row=1, column=0, sticky="nswe", padx=15, pady=5)

    def create_entries_widgets(self, master):
        entries_array = []
        create_label(
            master,
            0,
            0,
            text="Movimientos a crear",
            font=("Helvetica", 16),
            sticky="w",
            columnspan=len(self.columns),
        )
        for index, column in enumerate(self.columns):
            create_label(master, 1, index, text=column)
        n_rows = len(self.data_new_movements)
        n_columns = len(self.columns)
        master.columnconfigure(tuple(range(1, n_columns)), weight=1)
        for i in range(n_rows):
            row_entries = []
            for j in range(n_columns):
                if j == 2:
                    entry = create_Combobox(
                        master,
                        ["entrada", "salida"],
                        row=i + 2,
                        column=j,
                        state="readonly",
                    )
                else:
                    entry = create_entry(master, row=i + 2, column=j)
                    entry.insert(0, f"{self.data_new_movements[i][j]}")
                row_entries.append(entry)
            row_entries[0].configure(state="readonly")
            entries_array.append(row_entries)
        self.entries = entries_array

    def recreate_entry(self, data_products=None, columns=None):
        self.data_new_movements = (
            data_products if data_products is not None else self.data_new_movements
        )
        self.columns = columns if columns is not None else self.columns
        for widget in self.frame_products.winfo_children():
            widget.destroy()
        self.create_entries_widgets(self.frame_products)

    def add_movements(self):
        pass

    def update_movements(self):
        pass
