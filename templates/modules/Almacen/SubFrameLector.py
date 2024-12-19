# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 25/oct/2024  at 13:52 $"

import json
from datetime import datetime
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from static.constants import format_date
from templates.Functions_GUI_Utils import (
    create_label,
    create_button,
    create_Combobox,
    create_entry,
)
from templates.daemons.Peripherals import SerialPortListener
from templates.misc.PortsSearcher import serial_ports
from templates.resources.methods.Aux_Inventory import (
    columns_inventory,
    columns_movements_widgets_lector,
)


class LectorScreenSelector(ttk.Toplevel):
    def __init__(self, master=None, **kw):
        super().__init__(master)
        self.ports, self.ports_d = serial_ports()
        self.columnconfigure(0, weight=1)
        self.screen = kw.get("screen", None)
        self.callback_lector = kw.get("callback_lector", None)
        self.title("Lector de Productos")
        self.resizable(True, True)
        self.geometry("800x600")
        # ---------------------------------Port selector-----------------------------------------
        frame_port = ttk.Frame(self)
        frame_port.grid(row=0, column=0, sticky="nswe")
        frame_port.columnconfigure((0, 1, 2), weight=1)
        create_label(frame_port, 0, 0, text="Puerto: ", sticky="e")
        values_ports = [
            f"{port}-->{port_d}" for port, port_d in zip(self.ports, self.ports_d)
        ]
        self.port_selector = ttk.Combobox(
            frame_port, values=values_ports, state="readonly"
        )
        self.port_selector.grid(row=0, column=1, sticky="we")
        self.port_selector.set(values_ports[0])
        kw["port"] = {
            "selector": self.port_selector,
            "ports": self.ports,
            "ports_d": self.ports_d,
            "callback": self.callback_lector,
        }
        create_button(frame_port, 0, 2, text="Actualizar", command=self.update_ports)
        # ---------------------------------SubWindows-------------------------------------------
        kw["on_save_callback"] = self.on_close_after_save
        match self.screen:
            case "inventory":
                self.frame_lector = InventoryLector(self, **kw)
                self.frame_lector.grid(row=1, column=0, sticky="nsew")
            case "movements_in":
                kw["screen"] = "movements_in"
                self.frame_lector = MovementsLector(self, **kw)
                self.frame_lector.grid(row=1, column=0, sticky="nsew")
            case "movements_out":
                kw["screen"] = "movements_out"
                self.frame_lector = MovementsLector(self, **kw)
                self.frame_lector.grid(row=1, column=0, sticky="nsew")
            case _:
                create_label(self, 1, 0, text="No hay ventana para mostrar")
        # -----------------------------------Close Settings--------------------------------------
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grab_set()

    def on_close(self):
        msg = "¿Desea cerrar la ventana?"
        if messagebox.askyesno("Cerrar ventana", msg):
            if self.frame_lector.port_listener is not None:
                self.frame_lector.port_listener.stop()
            self.destroy()

    def update_ports(self):
        self.ports, self.ports_d = serial_ports()
        values_ports = [
            f"{port}-->{port_d}" for port, port_d in zip(self.ports, self.ports_d)
        ]
        self.port_selector.configure(values=values_ports)
        self.port_selector.set(values_ports[0])
        self.frame_lector.port_selector = self.port_selector
        self.frame_lector.ports = self.ports
        self.frame_lector.ports_d = self.ports_d

    def on_close_after_save(self):
        if self.frame_lector.port_listener is not None:
            self.frame_lector.port_listener.stop()
        self.destroy()


class InventoryLector(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master)
        self.ports, self.ports_d = serial_ports()
        self.btn_listen = None
        self.port_listener = None
        self.callback_lector = kw.get("callback_lector", None)
        self.on_save_callback = kw.get("on_save_callback", None)
        self.entries = None
        self.categories_dict = kw.get("categories_dict", {})
        self.providers_dict = kw.get("providers_dict", {})
        self.brands_dict = kw.get("brands_dict", {})
        self.ids_product_added = []
        self.svar_error = ttk.StringVar(value="")
        self.dict_old_stock = {}
        self.port_selector = kw["port"]["selector"]
        self.ports = kw["port"]["ports"]
        self.ports_d = kw["port"]["ports_d"]
        self.columnconfigure((0, 1), weight=1)
        self.data_products_gen = (
            kw["data_products_gen"] if "data_products_gen" in kw else []
        )
        self.data_products = []
        self.columns = columns_inventory
        # create_button(self, 6, 0, "Guardar", command=self.on_save_click, sticky="n", width=15)
        self.frame_products = ScrolledFrame(self, autohide=True)
        self.frame_products.grid(
            row=0, column=0, columnspan=2, sticky="we", padx=(5, 10)
        )
        self.create_entries_widgets(self.frame_products)
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=1, column=0, sticky="nswe", padx=(30, 30))
        self.create_btns(frame_buttons)
        frame_error = ttk.Frame(self)
        frame_error.grid(row=2, column=0, sticky="nswe", padx=(30, 30))
        create_label(frame_error, 0, 0, textvariable=self.svar_error, style="danger")

    def create_btns(self, master):
        self.btn_listen = create_button(
            master, 0, 0, sticky="n", text="Agregar items", command=self.add_registry
        )
        create_button(
            master, 0, 1, sticky="n", text="Guardar", command=self.on_save_click
        )

    def create_entries_widgets(self, master):
        entries_array = []
        for index, column in enumerate(self.columns):
            create_label(master, 0, index + 1, text=column)
        n_rows = len(self.data_products)
        n_columns = len(self.columns)
        master.columnconfigure(tuple(range(1, n_columns + 1)), weight=1)
        for i in range(n_rows):
            row_entries = []
            # noinspection PyArgumentList
            checkbutton = ttk.Checkbutton(master, text="", bootstyle="round-toggle")
            checkbutton.grid(row=i + 1, column=0)
            for j in range(n_columns):
                if j == 5:
                    entry = create_Combobox(
                        master,
                        values=list(self.categories_dict.keys()),
                        row=i + 1,
                        column=j + 1,
                    )
                    entry.set(self.data_products[i][j])
                elif j == 6:
                    entry = create_Combobox(
                        master,
                        values=list(self.providers_dict.keys()),
                        row=i + 1,
                        column=j + 1,
                    )
                    entry.bind(
                        "<<ComboboxSelected>>",
                        lambda event: self._on_provider_selected(event, i),
                    )
                    entry.set(self.data_products[i][j])
                elif j == 11:
                    entry = create_Combobox(
                        master,
                        values=[],
                        row=i + 1,
                        column=j + 1,
                        state="normal",
                    )
                    entry.set(self.data_products[i][j])
                else:
                    entry = create_entry(master, row=i + 1, column=j + 1)
                    entry.insert(0, f"{self.data_products[i][j]}")
                row_entries.append(entry)
            row_entries[0].configure(state="readonly")
            entries_array.append(row_entries)
        self.entries = entries_array

    def _on_provider_selected(self, event, index_row):
        provider_selected = event.widget.get()
        print(self.brands_dict)
        self.entries[index_row][11].configure(
            values=self.brands_dict[provider_selected]
        )

    def recreate_entry(self, data_products=None, columns=None):
        self.data_products = (
            data_products if data_products is not None else self.data_products
        )
        self.columns = columns if columns is not None else self.columns
        for widget in self.frame_products.winfo_children():
            widget.destroy()
        self.create_entries_widgets(self.frame_products)

    def add_registry(self):
        if self.port_listener is None:
            port_selected = self.port_selector.get().split("-->")[0]
            self.port_listener = SerialPortListener(
                port_selected,
                9600,
                self.product_detected_serial,
                self.serial_port_error_callback,
            )
            self.port_listener.start()
            self.btn_listen.configure(text="Detener")
            self.svar_error.set("")
        else:
            self.port_listener.stop()
            self.port_listener = None
            self.btn_listen.configure(text="Agregar items")

    def product_detected_serial(self, product):
        print(product)
        for index, item in enumerate(self.data_products_gen):
            codes = json.loads(item[9])
            locations = json.loads(item[10])
            brand = json.loads(item[11])
            if item[1] == product.upper() or product in codes:
                print("Encontrado")
                if item[1] in self.ids_product_added:
                    print("Ya agregado")
                    return
                self.ids_product_added.append(product.upper())
                self.data_products.append(
                    list(item[0:-3]) + [locations.get("location_1", ""), brand]
                )
                self.dict_old_stock[int(item[0])] = item[4]
                self.recreate_entry()
                return
        if product.upper() in self.ids_product_added:
            print("Ya agregado")
            return
        self.ids_product_added.append(product.upper())
        self.data_products.append(
            [
                "",
                product.upper(),
                "Name",
                "pza",
                "0",
                "None",
                "None",
                "0",
                "0",
                "[]",
                "",
                "",
            ]
        )
        self.recreate_entry()

    def on_save_click(self):
        if len(self.entries) <= 0:
            return
        products_update = []
        products_new = []
        for entry in self.entries:
            row = [entry[i].get() for i in range(len(entry))]
            if row[0] != "":
                row += [self.dict_old_stock[int(row[0])]]
                products_update.append(row)
            else:
                products_new.append(row)
        if self.callback_lector is None:
            print("No hay callback")
            return
        self.callback_lector((products_update, products_new))
        # close self
        self.on_save_callback() if self.on_save_callback is not None else self.master.destroy()
        # self.master.on_close_after_save()

    def serial_port_error_callback(self, error):
        print(error)
        self.port_listener.stop()
        self.port_listener = None
        self.btn_listen.configure(text="Agregar items")
        self.svar_error.set(error)


class MovementsLector(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master)
        self.ports, self.ports_d = serial_ports()
        self.btn_listen = None
        self.port_listener = None
        self.callback_lector = kw.get("callback_lector", None)
        self.on_save_callback = kw.get("on_save_callback", None)
        self.entries = None
        self.ids_product_added = []
        self.svar_error = ttk.StringVar(value="")
        self.port_selector = kw["port"]["selector"]
        self.ports = kw["port"]["ports"]
        self.ports_d = kw["port"]["ports_d"]
        self.screen = "entrada" if kw["screen"] == "movements_in" else "salida"
        self.columnconfigure((0, 1), weight=1)
        self.data_products_gen = (
            kw["data_products_gen"] if "data_products_gen" in kw else []
        )
        self.data_products = []
        self.columns = columns_movements_widgets_lector
        # create_button(self, 6, 0, "Guardar", command=self.on_save_click, sticky="n", width=15)
        self.frame_products = ScrolledFrame(self, autohide=True)
        self.frame_products.grid(
            row=0, column=0, columnspan=2, sticky="we", padx=(5, 10)
        )
        self.create_entries_widgets(self.frame_products)
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=1, column=0, sticky="nswe", padx=(30, 30))
        self.create_btns(frame_buttons)
        frame_error = ttk.Frame(self)
        frame_error.grid(row=2, column=0, sticky="nswe", padx=(30, 30))
        create_label(frame_error, 0, 0, textvariable=self.svar_error, style="danger")

    def create_btns(self, master):
        self.btn_listen = create_button(
            master, 0, 0, sticky="n", text="Agregar items", command=self.add_registry
        )
        create_button(
            master, 0, 1, sticky="n", text="Guardar", command=self.on_save_click
        )

    def create_entries_widgets(self, master):
        entries_array = []
        for index, column in enumerate(self.columns):
            create_label(master, 0, index + 1, text=column)
        n_rows = len(self.data_products)
        n_columns = len(self.columns)
        master.columnconfigure(tuple(range(1, n_columns + 1)), weight=1)
        for i in range(n_rows):
            row_entries = []
            # noinspection PyArgumentList
            checkbutton = ttk.Checkbutton(master, text="", bootstyle="round-toggle")
            checkbutton.grid(row=i + 1, column=0)
            for j in range(n_columns):
                entry = ttk.Entry(master)
                entry.grid(row=i + 1, column=j + 1, sticky="nsew")
                entry.insert(0, f"{self.data_products[i][j]}")
                row_entries.append(entry)
            row_entries[0].configure(state="readonly")
            entries_array.append(row_entries)
        self.entries = entries_array

    def recreate_entry(self, data_products=None, columns=None):
        self.data_products = (
            data_products if data_products is not None else self.data_products
        )
        self.columns = columns if columns is not None else self.columns
        for widget in self.frame_products.winfo_children():
            widget.destroy()
        self.create_entries_widgets(self.frame_products)

    def add_registry(self):
        if self.port_listener is None:
            port_selected = self.port_selector.get().split("-->")[0]
            self.port_listener = SerialPortListener(
                port_selected,
                9600,
                self.product_detected_serial,
                self.serial_port_error_callback,
            )
            self.port_listener.start()
            self.btn_listen.configure(text="Detener")
            self.svar_error.set("")
        else:
            self.port_listener.stop()
            self.port_listener = None
            self.btn_listen.configure(text="Agregar items")

    def product_detected_serial(self, product):
        if product == "\n" or product == "":
            return
        for item in self.data_products_gen:
            codes = json.loads(item[9])
            if item[1] == product.upper() or product.upper() in codes:
                print("Encontrado")
                if item[1] in self.ids_product_added:
                    print("Ya agregado")
                    return
                date = datetime.now().strftime(format_date)
                self.ids_product_added.append(item[1])
                self.data_products.append(
                    [item[0], item[2], self.screen, 0, date, "None", item[4], ""]
                )
                print(self.data_products)
                self.recreate_entry()
                return
        print("No encontrado")

    def on_save_click(self):
        if len(self.entries) <= 0:
            return
        products_new = []
        for entry in self.entries:
            row = [entry[i].get() for i in range(len(entry))]
            products_new.append((row[0], row[2], row[3], row[4], row[5], row[6]))
        if self.callback_lector is None:
            print("No hay callback")
            return
        self.callback_lector(products_new)
        self.on_save_callback() if self.on_save_callback is not None else self.master.destroy()

    def serial_port_error_callback(self, error):
        print(error)
        self.port_listener.stop()
        self.port_listener = None
        self.btn_listen.configure(text="Agregar items")
        self.svar_error.set(error)
