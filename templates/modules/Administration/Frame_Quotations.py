# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/jul./2024  at 15:07 $'

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.Functions_GUI_Utils import create_label, create_entry, create_Combobox, create_button


def create_input_widgets(master, data):
    frame_info = ttk.Frame(master)
    frame_info.grid(row=0, column=0, sticky="nswe")
    frame_info.columnconfigure((0, 1, 2, 3), weight=1)
    create_label(frame_info, 0, 0, text="Nombre compañia", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 0, 1, text="Usuario", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 0, 2, text="Telefono", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 0, 3, text="Email", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 2, 0, text="Planta", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 2, 1, text="Area", font=("Helvetica", 12, "normal"))
    create_label(frame_info, 2, 2, text="Ubicacion", font=("Helvetica", 12, "normal"))
    input_company = create_entry(frame_info, row=1, column=0, font=("Helvetica", 12, "normal"))
    input_user = create_entry(frame_info, row=1, column=1, font=("Helvetica", 12, "normal"))
    input_phone = create_entry(frame_info, row=1, column=2, font=("Helvetica", 12, "normal"))
    input_email = create_entry(frame_info, row=1, column=3, font=("Helvetica", 12, "normal"))
    input_planta = create_Combobox(frame_info, row=3, column=0, values=["Planta 1", "Planta 2"])
    input_area = create_Combobox(frame_info, row=3, column=1, values=["Area 1", "Area 2"])    
    input_ubicacion = create_entry(frame_info, row=3, column=2, font=("Helvetica", 12, "normal"))
    # ------------products------------
    frame_products = ttk.Frame(master)
    frame_products.grid(row=1, column=0, sticky="nswe")
    frame_products.columnconfigure((0, 1, 2, 3), weight=1)
    create_label(frame_products, 0, 0, text="Seleccion de Productos", font=("Helvetica", 16, "bold"), columnspan=4)
    create_label(frame_products, 1, 0, text="Producto", font=("Helvetica", 12, "normal"))
    create_label(frame_products, 1, 1, text="Cantidad", font=("Helvetica", 12, "normal"))
    create_label(frame_products, 1, 2, text="UDM", font=("Helvetica", 12, "normal"))
    create_label(frame_products, 1, 3, text="Precion (U)", font=("Helvetica", 12, "normal"))
    list_products = [item[2] for item in data]
    input_product_name = create_Combobox(frame_products, row=2, column=0, values=list_products)
    input_quantity = create_entry(frame_products, row=2, column=1, font=("Helvetica", 12, "normal"))
    input_udm = create_Combobox(frame_products, row=2, column=2, values=["KG", "LT", "ML"])
    input_price = create_entry(frame_products, row=2, column=3, font=("Helvetica", 12, "normal"))
    return [input_company, input_user, input_phone, input_email, input_planta, input_area, input_ubicacion,
            input_product_name, input_quantity, input_udm, input_price]


class QuotationsFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.id_product = None
        self.coldata = None
        self.table_widgets = None
        self.data_products = kwargs["data"]["data_products_gen"] if "data_products_gen" in kwargs["data"] else []
        # -----------------Title-------------------------------
        create_label(self, 0, 0, text="Cotizaciones", font=("Helvetica", 30, "bold"), columnspan=1)
        # -----------------Inputs------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure(0, weight=1)
        self.entries = create_input_widgets(frame_inputs, self.data_products)
        self.product_selector = self.entries[7]
        self.product_selector.bind("<<ComboboxSelected>>", self.product_selected)
        # -----------------Buttons-----------------------------
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=2, column=0, sticky="nswe")
        frame_buttons.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.create_button_widgets(frame_buttons)
        # -----------------Table-------------------------------
        frame_table = ttk.Frame(self)
        frame_table.grid(row=3, column=0, sticky="nswe")
        frame_table.rowconfigure(0, weight=1)
        self.table_widgets = self.create_table_widgets(frame_table)
        # -----------------btns procces------------------------------
        frame_procces = ttk.Frame(self)
        frame_procces.grid(row=4, column=0, sticky="nswe")
        frame_procces.columnconfigure((0, 1, 2, 3), weight=1)
        self.create_procces_btns(frame_procces)

    def create_button_widgets(self, frame_buttons):
        create_button(frame_buttons, 0, 0, sticky="n", text="Insertar", command=self.insert_product)
        create_button(frame_buttons, 0, 1, sticky="n", text="Actualizar", command=self.update_product)
        create_button(frame_buttons, 0, 2, sticky="n", text="Eliminar", command=self.delete_product)
        create_button(frame_buttons, 0, 3, sticky="n", text="Limpiar", command=self.clear_inputs)
        create_button(frame_buttons, 0, 4, sticky="n", text="Nuevo", command=self.new_product)

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
        data = [number, self.id_product, name, quantity, udm, price, float(quantity)*float(price)]
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
                data = [self._number_product, self.id_product, name, quantity, udm, price, float(quantity)*float(price)]
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
                item.delete(0, 'end')

    def new_product(self):
        pass

    def create_table_widgets(self, master):
        self.table_widgets.destroy() if self.table_widgets is not None else None
        coldata = []
        columns = ["#", "ID", "Descripcion", "Cantidad", "UDM", "Precio unitario", "Total"]
        for column in columns:
            if "Descripcion" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "#" in column:
                coldata.append({"text": column, "stretch": False, "width": 25})
            else:
                coldata.append({"text": column, "stretch": True})
        self.coldata = coldata
        data = []
        table_notifications = Tableview(master,
                                        coldata=coldata,
                                        autofit=False,
                                        paginated=False,
                                        searchable=False,
                                        rowdata=data,
                                        height=15)
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
        create_button(master, 0, 0, sticky="n", text="Crear", command=self.create_quotation)
        create_button(master, 0, 1, sticky="n", text="Guardar", command=self.save_quotation)
        create_button(master, 0, 2, sticky="n", text="Imprimir", command=self.print_quotation)
        create_button(master, 0, 3, sticky="n", text="Generar PDF", command=self.generate_pdf_quotation)

    def create_quotation(self):
        print("create")

    def save_quotation(self):
        print("save")

    def print_quotation(self):
        print("print")

    def generate_pdf_quotation(self):
        print("pdf")
