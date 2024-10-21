# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/jul./2024  at 15:07 $"

import json
from datetime import datetime
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from static.extensions import format_timestamps
from templates.Functions_GUI_Utils import (
    create_label,
    create_entry,
    create_Combobox,
    create_button,
)
from templates.controllers.contracts.quotations_controller import (
    update_quotation,
    get_quotation,
    create_quotation,
)
from templates.resources.methods.Functions_Aux_Admin import read_exel_products_bidding


def get_quotations():
    flag, error, data_quotations = get_quotation(None)
    return data_quotations


def get_data_entries(entries):
    data = [item.get() for item in entries]
    return data


def clean_entries(entries):
    for item in entries:
        if isinstance(item, ttk.Entry):
            item.delete(0, "end")
        elif isinstance(item, ttk.Combobox):
            item.set("")
        else:
            pass


def update_products_from_entries(entries_values, products_list):
    partidas = [int(item[0]) for item in entries_values]
    products_out = []
    for product in products_list:
        if product["partida"] in partidas:
            index = partidas.index(product["partida"])
            product["description"] = entries_values[index][1]
            product["quantity"] = float(entries_values[index][2])
            product["udm"] = entries_values[index][3]
            product["client"] = entries_values[index][4]
            product["date_needed"] = entries_values[index][5]
            products_out.append(product)
    return products_out


def update_info_from_entries(entries_values, info):
    info["company"] = entries_values[0]
    info["user"] = entries_values[1]
    info["phone"] = entries_values[2]
    info["email"] = entries_values[3]
    info["area"] = entries_values[4]
    info["location"] = entries_values[5]
    return info


def update_procedure(id_bidding, data_bidding, data_info, products):
    metadata = json.loads(data_bidding[1])
    metadata = update_info_from_entries(data_info, metadata)
    products_old = json.loads(data_bidding[2])
    products_new = update_products_from_entries(products, products_old)
    timestamps = json.loads(data_bidding[4])
    date_now = datetime.now().strftime(format_timestamps)
    timestamps["update"].append(date_now)
    flag, error, result = update_quotation(
        id_bidding, metadata, products_new, timestamps
    )
    return flag, error, result


def create_procedure(data_info, products):
    metadata = {
        "emission": datetime.now().strftime(format_timestamps),
        "limit_date": "",
        "quotation_code": "",
        "codigo": "",
        "company": data_info[0],
        "user": data_info[1],
        "phone": data_info[2],
        "email": data_info[3],
        "planta": "",
        "area": data_info[4],
        "location": data_info[5],
        "client_id": "",
    }
    flag, error, result = create_quotation(metadata, products)
    return flag, error, result


def finalize_action(self, flag, error, result):
    if flag:
        print("ok")
        clean_entries(self.entries)
        self.id_bidding = None
        self.data_bidding = None
        self.frame_products.recreate_entries([], self.columns)
    else:
        print(error)


def create_input_info_widgets(master):
    frame_info = master
    frame_info.columnconfigure((0, 1, 2, 3), weight=1)
    create_label(
        frame_info, 0, 0, text="Nombre compañia", font=("Helvetica", 12, "normal")
    )
    create_label(frame_info, 0, 1, text="Usuario", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 0, 2, text="Telefono", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 0, 3, text="Email", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 2, 0, text="Area", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 2, 1, text="Ubicacion", font=("Helvetica", 12, "normal"))
    input_company = create_entry(
        frame_info, row=1, column=0, font=("Helvetica", 12, "normal")
    )
    input_user = create_entry(
        frame_info, row=1, column=1, font=("Helvetica", 12, "normal")
    )
    input_phone = create_entry(
        frame_info, row=1, column=2, font=("Helvetica", 12, "normal")
    )
    input_email = create_entry(
        frame_info, row=1, column=3, font=("Helvetica", 12, "normal")
    )
    input_area = create_Combobox(
        frame_info, row=3, column=0, values=["Area 1", "Area 2"]
    )
    input_ubicacion = create_entry(
        frame_info, row=3, column=1, font=("Helvetica", 12, "normal")
    )
    return [
        input_company,
        input_user,
        input_phone,
        input_email,
        input_area,
        input_ubicacion,
    ]


def create_input_widgets(master, data):
    # ------------products------------
    frame_products = master
    frame_products.columnconfigure((0, 1, 2, 3), weight=1)
    create_label(
        frame_products,
        0,
        0,
        text="Seleccion de Productos",
        font=("Helvetica", 16, "bold"),
        columnspan=4,
    )
    create_label(
        frame_products, 1, 0, text="Producto", font=("Helvetica", 12, "normal")
    )
    create_label(
        frame_products, 1, 1, text="Cantidad", font=("Helvetica", 12, "normal")
    )
    create_label(frame_products, 1, 2, text="UDM", font=("Helvetica", 12, "normal"))
    create_label(
        frame_products, 1, 3, text="Precion (U)", font=("Helvetica", 12, "normal")
    )
    list_products = [item[2] for item in data]
    input_product_name = create_Combobox(
        frame_products, row=2, column=0, values=list_products
    )
    input_quantity = create_entry(
        frame_products, row=2, column=1, font=("Helvetica", 12, "normal")
    )
    input_udm = create_Combobox(
        frame_products, row=2, column=2, values=["KG", "LT", "ML"]
    )
    input_price = create_entry(
        frame_products, row=2, column=3, font=("Helvetica", 12, "normal")
    )
    return [
        input_product_name,
        input_quantity,
        input_udm,
        input_price,
    ]


class QuotationsBiddingsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nswe")
        notebook.columnconfigure(0, weight=1)

        # frame quotation
        frame_quotation = QuotationsFrame(notebook, **kwargs)
        notebook.add(frame_quotation, text="Cotizaciones")

        # frame bidding
        frame_bidding = BiddingsFrame(notebook, **kwargs)
        notebook.add(frame_bidding, text="Licitación")


class QuotationsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.id_product = None
        self.coldata = None
        self.table_widgets = None
        self.data_products = (
            kwargs["data"]["data_products_gen"]
            if "data_products_gen" in kwargs["data"]
            else []
        )
        # -----------------Title-------------------------------
        create_label(
            self,
            0,
            0,
            text="Cotizaciones",
            font=("Helvetica", 30, "bold"),
            columnspan=1,
        )
        # -----------------Inputs------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        entries_inf = create_input_info_widgets(frame_inputs)
        frame_products = ttk.Frame(self)
        frame_products.grid(row=2, column=0, sticky="nswe")
        entries_prod = create_input_widgets(frame_products, self.data_products)
        self.entries = entries_inf + entries_prod
        self.product_selector = self.entries[7]
        self.product_selector.bind("<<ComboboxSelected>>", self.product_selected)
        # -----------------Buttons-----------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=3, column=0, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.create_button_widgets(frame_buttons)
        # -----------------Table-------------------------------
        frame_table = ttk.Frame(self)
        frame_table.grid(row=4, column=0, sticky="nswe")
        frame_table.rowconfigure(0, weight=1)
        self.table_widgets = self.create_table_widgets(frame_table)
        # -----------------btns procces------------------------------
        frame_procces = ttk.Frame(self)
        frame_procces.grid(row=5, column=0, sticky="nswe")
        frame_procces.columnconfigure((0, 1, 2, 3), weight=1)
        self.create_procces_btns(frame_procces)

    def create_button_widgets(self, frame_buttons):
        create_button(
            frame_buttons,
            0,
            0,
            sticky="n",
            text="Insertar",
            command=self.insert_product,
        )
        create_button(
            frame_buttons,
            0,
            1,
            sticky="n",
            text="Actualizar",
            command=self.update_product,
        )
        create_button(
            frame_buttons,
            0,
            2,
            sticky="n",
            text="Eliminar",
            command=self.delete_product,
        )
        create_button(
            frame_buttons, 0, 3, sticky="n", text="Limpiar", command=self.clear_inputs
        )
        create_button(
            frame_buttons, 0, 4, sticky="n", text="Nuevo", command=self.new_product
        )

    def product_selected(self, event):
        for item in self.data_products:
            if item[2] == self.product_selector.get():
                self.entries[9].set(item[3])
                self.id_product = int(item[0])
                break

    def get_data_entries(self):
        data = [item.get() for item in self.entries]
        return data

    def insert_product(self):
        data = self.get_data_entries()
        name = self.entries[7].get()
        quantity = self.entries[8].get()
        udm = self.entries[9].get()
        price = self.entries[10].get()
        price = price if price != "" else 0.0
        items = self.table_widgets.view.get_children()
        number = len(items) + 1
        data = [
            number,
            self.id_product,
            name,
            quantity,
            udm,
            price,
            float(quantity) * float(price),
        ]
        self.table_widgets.insert_row(values=data)

    def update_product(self):
        items = self.table_widgets.view.get_children()
        for item in items:
            values = self.table_widgets.view.item(item, "values")
            if values[0] == self._number_product:
                data = self.get_data_entries()
                name = self.entries[7].get()
                quantity = self.entries[8].get()
                udm = self.entries[9].get()
                price = self.entries[10].get()
                data = [
                    self._number_product,
                    self.id_product,
                    name,
                    quantity,
                    udm,
                    price,
                    float(quantity) * float(price),
                ]
                self.table_widgets.view.item(item, values=data)
                break

    def delete_product(self):
        items = self.table_widgets.view.get_children()
        for item in items:
            values = self.table_widgets.view.item(item, "values")
            if values[0] == self._number_product:
                self.table_widgets.view.delete(item)
                break

    def clear_inputs(self):
        for item in self.entries:
            if isinstance(item, ttk.Combobox):
                item.set("")
            else:
                item.delete(0, "end")

    def new_product(self):
        pass

    def create_table_widgets(self, master):
        self.table_widgets.destroy() if self.table_widgets is not None else None
        coldata = []
        columns = [
            "#",
            "ID",
            "Descripcion",
            "Cantidad",
            "UDM",
            "Precio unitario",
            "Total",
        ]
        for column in columns:
            if "Descripcion" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "#" in column:
                coldata.append({"text": column, "stretch": False, "width": 25})
            else:
                coldata.append({"text": column, "stretch": True})
        self.coldata = coldata
        data = []
        table_notifications = Tableview(
            master,
            coldata=coldata,
            autofit=False,
            paginated=False,
            searchable=False,
            rowdata=data,
            height=15,
        )
        table_notifications.grid(row=1, column=0, sticky="nswe", padx=(5, 30))
        table_notifications.view.bind("<Double-1>", self._on_double_click_table)
        columns_header = table_notifications.get_columns()
        for item in columns_header:
            if item.headertext in ["id"]:
                item.hide()
        return table_notifications

    def _on_double_click_table(self, event):
        data = event.widget.item(event.widget.selection(), "values")
        self._number_product = data[0]
        print(data)

    def create_procces_btns(self, master):
        create_button(
            master, 0, 0, sticky="n", text="Crear", command=self.create_quotation
        )
        create_button(
            master, 0, 1, sticky="n", text="Guardar", command=self.save_quotation
        )
        create_button(
            master, 0, 2, sticky="n", text="Imprimir", command=self.print_quotation
        )
        create_button(
            master,
            0,
            3,
            sticky="n",
            text="Generar PDF",
            command=self.generate_pdf_quotation,
        )

    def create_quotation(self):
        print("create")

    def save_quotation(self):
        print("save")

    def print_quotation(self):
        print("print")

    def generate_pdf_quotation(self):
        print("pdf")


class BiddingsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.data_bidding = None
        self.id_bidding = None
        self.columnconfigure(0, weight=1)
        self.id_product = None
        self.coldata = None
        self.table_widgets = None
        self.data_biddings = (
            kwargs["data"]["quotations"] if "quotations" in kwargs["data"] else []
        )
        # -----------------Title-------------------------------
        create_label(
            self, 0, 0, text="Licitación", font=("Helvetica", 30, "bold"), columnspan=1
        )
        # -----------------Inputs------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure(0, weight=1)
        self.entries = create_input_info_widgets(frame_inputs)
        # -----------------Buttons-----------------------------
        frame_selector = ttk.Frame(self)
        frame_selector.grid(row=2, column=0, sticky="nswe")
        frame_selector.columnconfigure((0, 1), weight=1)
        self.entries_file_selector = self.create_file_selector(frame_selector)
        self.entries_file_selector[1].bind("<<ComboboxSelected>>", self.select_registry)
        # -----------------Products----------------------------
        self.columns = ["Partida", "Producto", "Cantidad", "UDM", "Cliente", "Fecha"]
        self.frame_products = SubFrameProducts(self, [], self.columns)
        self.frame_products.grid(row=3, column=0, sticky="nswe")
        self.entries_products = self.frame_products.get_entries_widgets()
        # -----------------btns procces------------------------------
        frame_procces = ttk.Frame(self)
        frame_procces.grid(row=4, column=0, sticky="nswe")
        frame_procces.columnconfigure((0, 1, 2, 3), weight=1)
        self.create_procces_btns(frame_procces)

    def create_file_selector(self, master):
        create_label(master, 0, 0, text="Seleccionar archivo")
        button_select = create_button(
            master,
            0,
            1,
            text="Seleccionar",
            command=self.select_file_bidding,
            sticky="n",
        )
        create_label(master, 1, 0, text="Seleccionar desde la DB")
        bidding_list = [f"{item[0]}" for item in self.data_biddings]
        select_db = create_Combobox(
            master, row=1, column=1, values=bidding_list, state="readonly", sticky="n"
        )
        return [button_select, select_db]

    def select_registry(self, event):
        selected = self.entries_file_selector[1].get()
        products = []
        for item in self.data_biddings:
            if str(item[0]) == selected:
                products = json.loads(item[2])
                self.id_bidding = item[0]
                self.data_bidding = item
                break
        data_table = []
        for product in products:
            data_table.append(
                [
                    product["partida"],
                    product["description"],
                    product["quantity"],
                    product["udm"],
                    "",
                    "",
                ]
            )
        self.frame_products.recreate_entries(data_table, self.columns)

    def select_file_bidding(self):
        filepath = filedialog.askopenfilename()
        if filepath == "":
            return
        data = read_exel_products_bidding(filepath)
        data_table = []
        for item in data:
            data_table.append(
                [
                    item["partida"],
                    item["description_small"],
                    item["quantity"],
                    item["udm"],
                    item["client"],
                    item["date_needed"],
                ]
            )
        # print(data)
        # data_dummy = [["name 1", 1, "udm", 10.0], ["name 2", 2, "udm", 20.0]]
        self.frame_products.recreate_entries(data_table, self.columns)
        self.id_bidding = None

    def create_procces_btns(self, master):
        create_button(
            master, 0, 0, sticky="n", text="Crear", command=self.create_quotation
        )
        create_button(
            master, 0, 1, sticky="n", text="Guardar", command=self.update_quotation
        )
        create_button(
            master,
            0,
            2,
            sticky="n",
            text="Generar PDF",
            command=self.generate_pdf_quotation,
        )

    def create_quotation(self):
        data_info = get_data_entries(self.entries)
        if self.id_bidding is None:
            print("create")
            products = self.frame_products.get_values_entries()
            flag, error, result = create_procedure(data_info, products)
        else:
            print("update")
            products = self.frame_products.get_values_entries()
            flag, error, result = update_procedure(
                self.id_bidding, self.data_bidding, data_info, products
            )
        finalize_action(self, flag, error, result)

    def update_quotation(self):
        if self.id_bidding is None:
            return
        data_info = get_data_entries(self.entries)
        products = self.frame_products.get_values_entries()
        flag, error, result = update_procedure(
            self.id_bidding, self.data_bidding, data_info, products
        )
        finalize_action(self, flag, error, result)

    def generate_pdf_quotation(self):
        print("pdf")


class SubFrameProducts(ttk.Frame):
    def __init__(self, master, data_products, columns, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        # title
        self.entries = None
        create_label(
            self,
            0,
            0,
            text="Productos",
            font=("Helvetica", 20, "bold"),
            columnspan=1,
        )
        self.data_products = data_products
        self.columns = columns
        self.frame_products = ScrolledFrame(self, autohide=True)
        self.frame_products.grid(row=1, column=0, sticky="nswe", padx=(5, 10))
        self.create_entries_widgets(self.frame_products)
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, sticky="nswe", padx=(30, 30))
        self.create_btns(frame_buttons)

    def create_btns(self, master):
        create_button(
            master, 0, 0, sticky="n", text="Agregar item", command=self.add_registry
        )

    def add_registry(self):
        pass

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
                entry.insert(0, self.data_products[i][j])
                row_entries.append(entry)
            entries_array.append(row_entries)
        self.entries = entries_array

    def get_values_entries(self):
        values = []
        for row in self.entries:
            row_values = [entry.get() for entry in row]
            values.append(row_values)
        return values

    def recreate_entries(self, data_products, columns):
        self.data_products = data_products
        self.columns = columns
        for widget in self.frame_products.winfo_children():
            widget.destroy()
        self.create_entries_widgets(self.frame_products)

    def get_entries_widgets(self):
        return self.entries
