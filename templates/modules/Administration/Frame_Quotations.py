# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 01/jul./2024  at 15:07 $"

import json
from datetime import datetime
from tkinter import filedialog

import pytz
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from static.constants import (
    format_timestamps,
    timezone_software,
    format_date,
    log_file_admin,
)
from templates.Functions_GUI_Utils import (
    create_label,
    create_entry,
    create_Combobox,
    create_button,
    create_ComboboxSearch,
    create_date_entry,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.contracts.quotations_controller import (
    update_quotation,
    get_quotation,
    create_quotation,
)
from templates.misc.Functions_Files import write_log_file
from templates.resources.methods.Functions_Aux_Admin import read_exel_products_bidding


def get_quotations():
    flag, error, data_quotations = get_quotation(None)
    return data_quotations


def get_data_entries(entries):
    data = [item.get() for item in entries]
    return data


def get_data_info_entries(entries):
    company_text = entries[0].get().split("-")
    try:
        if len(company_text) > 1:
            company = company_text[1]
            company_id = int(company_text[0])
        else:
            company = company_text[0]
            company_id = "None"
    except Exception as e:
        print(e)
        company = entries[0].get()
        company_id = "None"
    user = entries[1].get()
    phone = entries[2].get()
    email = entries[3].get()
    area = entries[4].get()
    location = entries[5].get()
    return company, user, phone, email, area, location, company_id


def get_data_products_entries(entries):
    name = entries[6].get()
    quantity = entries[7].get()
    udm = entries[8].get()
    price = entries[9].get()
    date = entries[10].entry.get()
    quantity = quantity if quantity != "" else 0.0
    price = price if price != "" else 0.0
    return name, quantity, udm, price, date


def clean_entries(entries):
    for item in entries:
        if isinstance(item, ttk.Entry):
            item.delete(0, "end")
        elif isinstance(item, ttk.Combobox):
            item.set("")
        elif isinstance(item, ttk.DateEntry):
            date_now = datetime.now().strftime(format_date)
            item.entry.delete(0, "end")
            item.entry.insert(0, date_now)
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
    info["company"] = (entries_values[0],)
    info["user"] = (entries_values[1],)
    info["phone"] = (entries_values[2],)
    info["email"] = (entries_values[3],)
    info["area"] = (entries_values[4],)
    info["location"] = (entries_values[5],)
    info["client_id"] = (entries_values[6],)
    return info


def update_procedure_quoation(
    id_bidding, metadata_bidding, data_info, products: list[dict], userdata
):
    metadata = json.loads(metadata_bidding[1])
    metadata = update_info_from_entries(data_info, metadata)
    products_old = json.loads(metadata_bidding[2])
    products_new = update_products_from_entries(products, products_old)
    timestamps = json.loads(metadata_bidding[4])
    time_zone = pytz.timezone(timezone_software)
    date_now = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    timestamps["update"].append({"date": date_now, "user": userdata["id"]})
    flag, error, result = update_quotation(
        id_bidding, metadata, products_new, timestamps
    )
    return flag, error, result


def create_procedure(data_info, products: list[dict], userdata, status):
    time_zone = pytz.timezone(timezone_software)
    timestamp = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_timestamps)
    metadata = {
        "emission": timestamp,
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
        "client_id": data_info[6],
        "user_id": userdata["id"],
    }
    flag, error, result = create_quotation(metadata, products, status=status)
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


def create_input_info_widgets(master, data_clients, style="TFrame"):
    style_l = style.split(".")
    bootstyle = f"{style_l[0]}.Inverse" if len(style_l) > 1 else None
    frame_info = master
    frame_info.columnconfigure((0, 1, 2, 3), weight=1)
    create_label(
        frame_info,
        0,
        0,
        text="Nombre compañia",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    create_label(
        frame_info,
        0,
        1,
        text="Usuario",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    create_label(
        frame_info,
        0,
        2,
        text="Telefono",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    create_label(
        frame_info,
        0,
        3,
        text="Email",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    create_label(
        frame_info, 2, 0, text="Area", font=("Helvetica", 12, "normal"), style=bootstyle
    )
    create_label(
        frame_info,
        2,
        1,
        text="Ubicacion",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    clients_list = [f"{client[0]}-{client[1]}" for client in data_clients]
    input_company = create_ComboboxSearch(
        frame_info, row=1, column=0, values=clients_list, state="normal"
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
        frame_info, row=3, column=0, values=["Area 1", "Area 2"], state="normal"
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


def create_input_widgets(master, data, style="TFrame"):
    style_l = style.split(".")
    bootstyle = f"{style_l[0]}.Inverse" if len(style_l) > 1 else None
    # ------------products------------
    frame_products = master
    frame_products.columnconfigure((0, 1, 2, 3, 4), weight=1)
    create_label(
        frame_products,
        0,
        0,
        text="Seleccion de Productos",
        font=("Helvetica", 16, "bold"),
        columnspan=4,
        style=f"{bootstyle}.TLalbel",
    )
    create_label(
        frame_products,
        1,
        0,
        text="Producto",
        font=("Helvetica", 12, "normal"),
        style=f"{bootstyle}.TLabel",
    )
    create_label(
        frame_products,
        1,
        1,
        text="Cantidad",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    create_label(
        frame_products,
        1,
        2,
        text="UDM",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    create_label(
        frame_products,
        1,
        3,
        text="Precion (U)",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    create_label(
        frame_products,
        1,
        4,
        text="Fecha",
        font=("Helvetica", 12, "normal"),
        style=bootstyle,
    )
    list_products = [item[2] for item in data]
    input_product_name = create_ComboboxSearch(
        frame_products, row=2, column=0, values=list_products, state="normal"
    )
    input_quantity = create_entry(
        frame_products, row=2, column=1, font=("Helvetica", 12, "normal")
    )
    input_udm = create_Combobox(
        frame_products, row=2, column=2, values=["KG", "LT", "ML"], state="normal"
    )
    input_price = create_entry(
        frame_products, row=2, column=3, font=("Helvetica", 12, "normal")
    )
    input_date = create_date_entry(
        frame_products,
        row=2,
        column=4,
        firstweekday=0,
        dateformat=format_date,
        startdate=None,
    )
    return [input_product_name, input_quantity, input_udm, input_price, input_date]


def create_dict_products(data, type_q="quotation"):
    products = []
    if type_q == "quotation":
        for item in data:
            product = {
                "id_p": item[1],
                "partida": item[0],
                "description_small": item[2],
                "quantity": item[3],
                "udm": item[4],
                "price_unit": item[5],
                "date_needed": item[7],
                "client": "",
                "marca": "",
                "type_p": "",
                "comment": "",
                "n_parte": "",
                "revision": "",
                "description": "",
            }
            products.append(product)
        return products
    else:
        for item in data:
            product = {
                "id_p": "None",
                "partida": item[0],
                "description_small": item[1],
                "quantity": item[2],
                "udm": item[3],
                "client": item[4],
                "date_needed": item[5],
                "marca": "",
                "type_p": "",
                "comment": "",
                "n_parte": "",
                "revision": "",
                "price_unit": "",
                "description": "",
            }
            products.append(product)
    return products


def end_action_quotations(msg, title, usernamedata):
    if msg is None or msg == "":
        return
    msg += f"\n[Usuario: {usernamedata.get('username', 'No username')}]"
    create_notification_permission_notGUI(
        msg, ["Administracion"], title, usernamedata["id"], 0
    )
    timestamp = datetime.now().strftime(format_timestamps)
    msg += f"[Timestamp: {timestamp}]"
    msg += f"[ID: {usernamedata.get('id', 'No id')}]"
    write_log_file(log_file_admin, msg)


class QuotationsBiddingsFrame(ScrolledFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, autohide=True)
        self.columnconfigure(0, weight=1)
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nswe", padx=(2, 10))
        notebook.columnconfigure(0, weight=1)

        # frame quotation
        frame_quotation = QuotationsFrame(notebook, **kwargs)
        notebook.add(frame_quotation, text="Cotizaciones FC")

        # frame bidding
        frame_bidding = BiddingsFrame(notebook, **kwargs)
        notebook.add(frame_bidding, text="Licitación")


class QuotationsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.id_quotation = None
        self.id_product = None
        self.columnconfigure(0, weight=1)
        self.coldata = None
        self.table_widgets = None
        self.data_products = kwargs["data"].get("data_products_gen", [])
        self.clients_data = kwargs["data"].get("data_clients_gen", [])
        self.usernamedata = kwargs.get("username_data", None)
        self.data_quotations = kwargs["data"].get("quotations", [])
        self._products_input = []
        # -----------------Title-------------------------------
        create_label(
            self,
            0,
            0,
            text="Cotizaciones",
            font=("Helvetica", 30, "bold"),
            columnspan=1,
        )
        # ---------------------Inputs and quotation selector---------------------------------
        style_info_ins = "TFrame"
        # bootstyle = style_info_ins.split(".")[0] + ".Inverse"
        bootstyle = None
        frame_ins = ttk.LabelFrame(self)
        frame_ins.grid(row=1, column=0, sticky="nswe", padx=10)
        frame_ins.columnconfigure(0, weight=1)
        frame_quotation_selector = ttk.Frame(frame_ins, style=style_info_ins)
        frame_quotation_selector.grid(row=0, column=0, sticky="nswe")
        frame_quotation_selector.columnconfigure(1, weight=1)
        create_label(
            frame_quotation_selector,
            0,
            0,
            text="Seleccion de cotizacion",
            style=bootstyle,
        )
        quotations_list = [
            f"{item[0]}-{item[-2]}-{item[-1]}" for item in self.data_quotations
        ]
        self.quoation_selector = create_ComboboxSearch(
            frame_quotation_selector,
            row=0,
            column=1,
            values=quotations_list,
            state="normal",
        )
        self.quoation_selector.bind("<<ComboboxSelected>>", self.quotation_selected)
        frame_inputs = ttk.Frame(frame_ins, style=style_info_ins)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure(0, weight=1)
        entries_inf = create_input_info_widgets(
            frame_inputs, self.clients_data, style=style_info_ins
        )
        frame_products = ttk.Frame(frame_ins, style=style_info_ins)
        frame_products.grid(row=2, column=0, sticky="nswe")
        entries_prod = create_input_widgets(
            frame_products, self.data_products, style=style_info_ins
        )
        self.entries = entries_inf + entries_prod
        self.product_selector = self.entries[6]
        self.product_selector.bind("<<ComboboxSelected>>", self.product_selected)
        # -----------------Buttons-----------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.create_button_widgets(frame_buttons)
        # -----------------Table-------------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=5, column=0, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        self.table_widgets = self.create_table_widgets()
        # -----------------btns procces------------------------------
        frame_procces = ttk.Frame(self)
        frame_procces.grid(row=6, column=0, sticky="nswe")
        frame_procces.columnconfigure((0, 1, 2), weight=1)
        self.create_procces_btns(frame_procces)

    def create_button_widgets(self, frame_buttons):
        create_button(
            frame_buttons,
            0,
            0,
            sticky="n",
            text="Agregar producto",
            command=self.insert_product,
        )
        create_button(
            frame_buttons,
            0,
            1,
            sticky="n",
            text="Actualizar producto",
            command=self.update_product,
        )
        create_button(
            frame_buttons,
            0,
            2,
            sticky="n",
            text="Eliminar producto",
            command=self.delete_product,
        )
        create_button(
            frame_buttons, 0, 3, sticky="n", text="Limpiar", command=self.clear_inputs
        )
        create_button(
            frame_buttons,
            0,
            4,
            sticky="n",
            text="Nuevo producto",
            command=self.new_product,
        )

    def product_selected(self, event):
        name = event.widget.get()
        for item in self.data_products:
            if item[2] == name:
                self.entries[8].set(item[3])
                self.id_product = int(item[0])
                break

    def insert_product(self):
        if self.id_product is None:
            print("No hay producto seleccionado")
            return
        name, quantity, udm, price, date = get_data_products_entries(self.entries)
        number = len(self._products_input) + 1
        data = [
            number,
            self.id_product,
            name,
            quantity,
            udm,
            float(price),
            float(quantity) * float(price),
            date,
        ]
        self._products_input.append(data)
        self.table_widgets = self.create_table_widgets()

    def update_product(self):
        for index, item in enumerate(self._products_input):
            if int(item[0]) == self._number_product:
                name, quantity, udm, price, date = get_data_products_entries(
                    self.entries
                )
                data = [
                    self._number_product,
                    self.id_product,
                    name,
                    quantity,
                    udm,
                    float(price),
                    float(quantity) * float(price),
                    date,
                ]
                self._products_input[index] = data
                break
        self.table_widgets = self.create_table_widgets()
        self.clear_inputs_product()
        self.id_product = None

    def delete_product(self):
        items = self._products_input.copy()
        counter = 0
        for index, item in enumerate(items):
            if int(item[0]) == self._number_product:
                self._products_input.remove(item)
                counter = item[0]
            else:
                print(counter)
                if counter != 0:
                    self._products_input[index - 1][0] = counter
                    counter += 1
        self.table_widgets = self.create_table_widgets()
        self.clear_inputs_product()
        self.id_product = None

    def clear_inputs(self):
        for item in self.entries:
            if isinstance(item, ttk.Combobox):
                item.set("")
            else:
                item.delete(0, "end")

    def clear_inputs_product(self):
        entries = self.entries[6:]
        for item in entries:
            if isinstance(item, ttk.Combobox):
                item.set("")
            elif isinstance(item, ttk.DateEntry):
                item.entry.delete(0, "end")
                item.entry.insert(0, "")
            else:
                item.delete(0, "end")

    def new_product(self):
        name, quantity, udm, price, date = get_data_products_entries(self.entries)
        number = len(self._products_input) + 1
        data = [
            number,
            None,
            name,
            quantity,
            udm,
            float(price),
            float(quantity) * float(price),
            date,
        ]
        self._products_input.append(data)
        self.table_widgets = self.create_table_widgets()

    def create_table_widgets(self):
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
            "Fecha requerida",
        ]
        for column in columns:
            if "Descripcion" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "#" in column:
                coldata.append({"text": column, "stretch": False, "width": 25})
            else:
                coldata.append({"text": column, "stretch": True})
        self.coldata = coldata
        data = self._products_input if self._products_input is not None else []
        table = Tableview(
            self.frame_table,
            coldata=coldata,
            autofit=False,
            paginated=False,
            searchable=False,
            rowdata=data,
            height=15,
        )
        table.grid(row=1, column=0, sticky="nswe", padx=(5, 30))
        table.view.bind("<Double-1>", self._on_double_click_table)
        columns_header = table.get_columns()
        for item in columns_header:
            if item.headertext in ["id"]:
                item.hide()
        return table

    def _on_double_click_table(self, event):
        data = event.widget.item(event.widget.selection(), "values")
        self._number_product = int(data[0])
        self.id_product = int(data[1]) if data[1] != "None" and data[1] != "" else None
        self.clear_inputs_product()
        self.entries[6].set(data[2])
        self.entries[7].insert(0, data[3])
        self.entries[8].set(data[4])
        self.entries[9].insert(0, data[5])
        self.entries[10].entry.insert(0, data[7])

    def create_procces_btns(self, master):
        create_button(
            master,
            0,
            0,
            sticky="n",
            text="Crear cotización",
            command=self.create_quotation,
        )
        create_button(
            master,
            0,
            1,
            sticky="n",
            text="Guardar borrador",
            command=self.save_quotation_scrap,
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
        data_info = get_data_info_entries(self.entries)
        data_products = create_dict_products(self._products_input, type_q="quotation")
        flag, error, result = create_procedure(
            data_info, data_products, self.usernamedata, status=1
        )
        if not flag:
            print(error)
            return
        msg = f"Creacion de cotizacion id: {result} status: {1}"
        end_action_quotations(msg, "Creacion de cotizacion", self.usernamedata)
        print(msg)
        self.reset_inputs()

    def save_quotation_scrap(self):
        data_info = get_data_info_entries(self.entries)
        data_products = create_dict_products(self._products_input, type_q="quotation")
        flag, error, result = create_procedure(
            data_info, data_products, self.usernamedata, status=0
        )
        if not flag:
            print(error)
            return
        msg = f"Creacion de cotizacion id: {result} status: {0}"
        end_action_quotations(msg, "Creacion de cotizacion", self.usernamedata)
        print(msg)
        self.reset_inputs()

    def update_quotation(self):
        data_info = get_data_info_entries(self.entries)
        data_products = create_dict_products(self._products_input, type_q="quotation")
        data_quotation = []
        for item in self.data_quotations:
            if item[0] == self.id_quotation:
                data_quotation = item
                break
        flag, error, result = update_procedure_quoation(
            self.id_quotation,
            data_quotation,
            data_info,
            data_products,
            self.usernamedata,
        )
        if not flag:
            print(error)
            return
        msg = f"Actualizacion de cotizacion id: {result}"
        end_action_quotations(msg, "Actualizacion de cotizacion", self.usernamedata)
        print(msg)
        self.reset_inputs()

    def generate_pdf_quotation(self):
        print("pdf")

    def reset_inputs(self):
        for item in self.entries:
            if isinstance(item, ttk.Combobox):
                item.set("")
            elif isinstance(item, ttk.DateEntry):
                item.entry.delete(0, "end")
            else:
                item.delete(0, "end")
        self._products_input = []
        self.id_product = None
        self.table_widgets = self.create_table_widgets()

    def quotation_selected(self, event):
        data = event.widget.get().split("-")
        self.id_quotation = int(data[0])


class BiddingsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.data_bidding = None
        self.id_bidding = None
        self.columnconfigure(0, weight=1)
        self.usernamedata = kwargs.get("username_data", None)
        self.id_product = None
        self.coldata = None
        self.table_widgets = None
        self.data_biddings = kwargs["data"].get("data_biddings_gen", [])
        self.clients_data = kwargs["data"].get("data_clients_gen", [])
        # -----------------Title-------------------------------
        create_label(
            self, 0, 0, text="Licitación", font=("Helvetica", 30, "bold"), columnspan=1
        )
        # -----------------Inputs------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure(0, weight=1)
        self.entries = create_input_info_widgets(frame_inputs, self.clients_data)
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
            flag, error, result = create_procedure(
                data_info, products, self.usernamedata
            )
        else:
            print("update")
            products = self.frame_products.get_values_entries()
            flag, error, result = update_procedure_quoation(
                self.id_bidding,
                self.data_bidding,
                data_info,
                products,
                self.usernamedata,
            )
        finalize_action(self, flag, error, result)

    def update_quotation(self):
        if self.id_bidding is None:
            return
        data_info = get_data_entries(self.entries)
        products = self.frame_products.get_values_entries()
        flag, error, result = update_procedure_quoation(
            self.id_bidding, self.data_bidding, data_info, products, self.usernamedata
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
            # noinspection PyArgumentList
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
