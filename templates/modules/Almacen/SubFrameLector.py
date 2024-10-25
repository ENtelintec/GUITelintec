# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 25/oct/2024  at 13:52 $"

import threading
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from templates.Functions_GUI_Utils import create_label, create_button
from templates.misc.PortsSearcher import serial_ports

columns_inventory = [
    "ID",
    "SKU",
    "Producto",
    "UDM",
    "Cantidad",
    "Categoria",
    "ID SM",
    "Herramienta?",
    "Interno?",
]


class ProductsLector(ttk.Toplevel):
    def __init__(self, master=None, **kw):
        super().__init__(master)
        self.ports, self.ports_d = serial_ports()
        self.title("Lector de Productos")
        self.resizable(True, True)
        self.geometry("800x600")
        self.columnconfigure(0, weight=1)
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
        }
        create_button(frame_port, 0, 2, text="Actualizar", command=self.update_ports)
        # ---------------------------------SubWindows-------------------------------------------
        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew")
        self.frame1 = InventoryLector(notebook, **kw)
        notebook.add(self.frame1, text="Inventario")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grab_set()

    def update_ports(self):
        self.ports, self.ports_d = serial_ports()
        values_ports = [
            f"{port}-->{port_d}" for port, port_d in zip(self.ports, self.ports_d)
        ]
        self.port_selector.configure(values=values_ports)
        self.port_selector.set(values_ports[0])
        self.frame1.port_selector = self.port_selector
        self.frame1.ports = self.ports
        self.frame1.ports_d = self.ports_d

    def on_close(self):
        msg = "¿Desea cerrar la ventana?"
        if messagebox.askyesno("Cerrar ventana", msg):
            if self.frame1.port_listener is not None:
                self.frame1.port_listener.stop()
            self.destroy()


class InventoryLector(ttk.Frame):
    def __init__(self, master=None, **kw):
        super().__init__(master)
        self.ports, self.ports_d = serial_ports()
        self.btn_listen = None
        self.port_listener = None
        self.entries = None
        self.ids_product_added = []
        self.port_selector = kw["port"]["selector"]
        self.ports = kw["port"]["ports"]
        self.ports_d = kw["port"]["ports_d"]
        self.columnconfigure((0, 1), weight=1)
        self.data_products_gen = (
            kw["data_products_gen"] if "data_products_gen" in kw else []
        )
        print(self.data_products_gen)
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

    def create_btns(self, master):
        self.btn_listen = create_button(
            master, 0, 0, sticky="n", text="Agregar items", command=self.add_registry
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
                port_selected, 9600, self.product_detected_serial
            )
            self.port_listener.start()
            self.btn_listen.configure(text="Detener")
        else:
            self.port_listener.stop()
            self.port_listener = None
            self.btn_listen.configure(text="Agregar items")

    def product_detected_serial(self, product):
        print(product)
        for item in self.data_products_gen:
            if item[1] == product:
                print("Encontrado")
                if product in self.ids_product_added:
                    print("Ya agregado")
                    return
                self.ids_product_added.append(product)
                self.data_products.append(item)
                self.recreate_entry()
                return
        self.ids_product_added.append(product)
        self.data_products.append(["", product, "", "", "", "", "", "", ""])
        self.recreate_entry()


class SerialPortListener(threading.Thread):
    def __init__(self, port, baudrate, callback):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.stop_event = threading.Event()

    def run(self):
        import serial

        with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
            while not self.stop_event.is_set():
                line = ser.readline().decode("utf-8").strip()
                if line:
                    self.callback(line)

    def stop(self):
        self.stop_event.set()
