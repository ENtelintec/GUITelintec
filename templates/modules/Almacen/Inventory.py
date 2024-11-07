import json
import time
from datetime import datetime
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from static.extensions import format_date
from templates.Functions_GUI_Utils import (
    create_label,
    create_entry,
    create_Combobox,
    create_button,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.product.p_and_s_controller import (
    insert_multiple_row_products_amc,
    update_multiple_row_products_amc,
    get_all_categories_db,
    insert_multiple_row_movements_amc,
    create_product_db,
    create_in_movement_db,
    update_product_db,
    get_all_products_db,
    delete_product_db,
)
from templates.controllers.supplier.suppliers_controller import get_all_suppliers_amc
from templates.forms.BarCodeGenerator import create_BarCodeFormat
from templates.forms.Storage import InventoryStorage
from templates.modules.Almacen.SubFrameBarcode import BarcodeFrame
from templates.modules.Almacen.SubFrameLector import LectorScreenSelector

coldata_inventory = [
    {"text": "ID Producto", "stretch": True},
    {"text": "SKU", "stretch": True},
    {"text": "Nombre", "stretch": True},
    {"text": "UDM", "stretch": True},
    {"text": "Stock", "stretch": True},
    {"text": "Categoría", "stretch": True},
    {"text": "Proveedor", "stretch": True},
    {"text": "Herramienta", "stretch": True},
    {"text": "Interno", "stretch": True},
    {"text": "Codigos", "stretch": True},
    {"text": "Ubicaciones", "stretch": True},
]


def fetch_products():
    flag, error, result = get_all_products_db()
    if not flag:
        print(error)
        return []
    return result


def get_row_data_inventory(data_raw):
    data = []
    for row in data_raw:
        codes = json.loads(row[9])
        data.append(
            (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                row[7],
                row[8],
                codes,
            )
        )
    return data


def get_providers_dict(data_raw):
    # id_supplier, name, seller_name, seller_email, phone, address, web_url, type
    data = {}
    for row in data_raw:
        data[row[1]] = row[0]
    return data


def get_categories_dict(data_raw):
    # id_supplier, name
    data = {}
    for row in data_raw:
        data[row[1]] = row[0]
    return data
    pass


def create_input_widgets(
    master, _ivar_tool, _ivar_internal, categories_dict, providers_dict_amc
):
    entries = []
    master.columnconfigure((0, 1, 2, 3, 4), weight=1)
    # Inputs left
    create_label(master, 0, 0, text="ID", sticky="w")
    input_id = create_entry(master, row=0, column=1)
    input_id.configure(state="disabled")
    entries.append(input_id)
    create_label(master, 1, 0, text="SKU", sticky="w")
    input_sku = create_entry(master, row=1, column=1)
    entries.append(input_sku)
    create_label(master, 2, 0, text="Nombre", sticky="w")
    input_name = create_entry(master, row=2, column=1)
    entries.append(input_name)
    create_label(master, 3, 0, text="UDM", sticky="w")
    input_udm = create_entry(master, row=3, column=1)
    entries.append(input_udm)
    create_label(master, 4, 0, text="Stock", sticky="w")
    input_stock = create_entry(master, row=4, column=1)
    entries.append(input_stock)
    create_label(master, 0, 2, text="Categoría", sticky="w")
    values_cat = list(categories_dict.keys())

    cat_selector = create_Combobox(master, values=values_cat, row=0, column=3)
    entries.append(cat_selector)
    create_label(master, 1, 2, text="Proveedor", sticky="w")
    values_supp = list(providers_dict_amc.keys())
    supp_selector = create_Combobox(master, values=values_supp, row=1, column=3)
    entries.append(supp_selector)
    # noinspection PyArgumentList
    ttk.Checkbutton(
        master,
        text="Es herramienta?",
        variable=_ivar_tool,
        onvalue=1,
        offvalue=0,
        bootstyle="success, round-toggle",
    ).grid(row=0, column=4, sticky="we", padx=5, pady=5, columnspan=2)
    entries.append(_ivar_tool)
    # noinspection PyArgumentList
    ttk.Checkbutton(
        master,
        text="Es interno?",
        variable=_ivar_internal,
        onvalue=1,
        offvalue=0,
        bootstyle="success, round-toggle",
    ).grid(row=1, column=4, sticky="we", padx=5, pady=5, columnspan=2)
    entries.append(_ivar_internal)
    create_label(master, 2, 2, text="Codigos", sticky="w")
    input_codes = create_entry(master, row=2, column=3)
    entries.append(input_codes)
    create_label(master, 3, 2, text="Ubicacion 1", sticky="w")
    input_location_1 = create_entry(master, row=3, column=3)
    entries.append(input_location_1)
    create_label(master, 4, 2, text="Ubicacion 2", sticky="w")
    input_location_2 = create_entry(master, row=4, column=3)
    entries.append(input_location_2)
    return entries


class InventoryScreen(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.old_stock = None
        self.table = None
        self.col_data = None
        self.id_to_modify = None
        self.master = master
        self.columnconfigure(0, weight=1)
        self._ivar_tool = ttk.IntVar(value=0)
        self._ivar_internal = ttk.IntVar(value=0)
        self._products = (
            fetch_products()
            if "data_products_gen" not in kwargs["data"]
            else kwargs["data"]["data_products_gen"]
        )
        flag, error, data_raw_providers = (
            get_all_suppliers_amc()
            if "data" not in kwargs
            else (True, None, kwargs["data"]["data_providers_gen"])
        )
        self._trigger_actions_main_callback = kwargs["triger_actions_main_callback"]
        self._providers_dict_amc = get_providers_dict(data_raw_providers)
        flag, error, data_raw_categories = (
            get_all_categories_db()
            if "data" not in kwargs
            else (True, None, kwargs["data"]["data_categories_gen"])
        )
        self._categories_dict = get_categories_dict(data_raw_categories)
        self._table = Tableview(self)
        # -------------------------------Title----------------------------------------------
        create_label(self, 0, 0, text="Inventario", font=("Helvetica", 22, "bold"))
        # -------------------------------Table-------------------------------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=2, column=0, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        ttk.Label(self.frame_table, text="Tabla de Productos", font=("Arial", 20)).grid(
            row=0, column=0, sticky="w", padx=5, pady=10
        )
        self.create_table(self.frame_table)
        # -------------------------------inputs-------------------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.entries = create_input_widgets(
            frame_inputs,
            self._ivar_tool,
            self._ivar_internal,
            self._categories_dict,
            self._providers_dict_amc,
        )
        # --------------------------------btns-------------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=3, column=0, sticky="nswe")
        frame_btns.columnconfigure((0, 1, 2, 3), weight=1)
        self.create_buttons(frame_btns)

    def create_table(self, master):
        if self.table is not None:
            self.table.destroy()
        self.col_data = coldata_inventory
        self.table = Tableview(
            master,
            bootstyle="primary",
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True,
            coldata=self.col_data,
            rowdata=self._products,
        )
        self.table.grid(row=1, column=0, sticky="nswe", padx=15, pady=5)
        self.table.view.bind("<Double-1>", self.on_click_table_item)

    def create_buttons(self, master):
        create_button(
            master,
            0,
            0,
            text="Agregar Producto",
            command=self.add_product,
            style="success",
        )
        create_button(
            master,
            0,
            1,
            text="Actualizar Producto",
            command=self.update_product,
            style="info",
        )
        create_button(
            master,
            0,
            2,
            text="Eliminar Producto",
            command=self.delete_product,
            style="warning",
        )
        create_button(
            master,
            0,
            3,
            text="Limpiar Campos",
            command=self.clear_fields,
        )
        create_button(
            master,
            1,
            0,
            text="Actualizar Tabla",
            command=self.update_table,
        )
        create_button(
            master,
            1,
            1,
            text="Lector",
            command=self.lector,
        )
        create_button(
            master,
            1,
            2,
            text="Imprimir listado",
            command=self.print_products,
        )
        create_button(
            master,
            1,
            3,
            text="Imprimir Codigo",
            command=self.print_code,
        )

    def print_code(self):
        if self.id_to_modify is None:
            return
        sku = self.entries[1].get()
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Guardar como",
        )
        if not filepath:
            return
        create_BarCodeFormat(sku, filepath, "128")
        kw = {
            "pdf_filepath": filepath,
        }
        BarcodeFrame(self, sku, **kw)

    def print_products(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Guardar como",
        )
        if not filepath:
            return
        # products = ["ID", "Description", "UDM", "Categoria", "Stock Min", "Stock", "Solicitar"]
        products = [
            (item[0], item[2], item[3], item[5], " ", item[4], " ")
            for item in self._products
        ]
        # sort by ID
        products.sort(key=lambda x: x[0])
        InventoryStorage(
            dict_data={"filename_out": filepath, "products": products},
            type_form="Materials",
        )
        print(f"Se guardo el pdf en: {filepath}")

    def lector(self):
        data = {
            "data_products_gen": self._products,
            "screen": "inventory",
            "callback_lector": self.save_data_lector,
        }
        LectorScreenSelector(self, **data)

    def save_data_lector(self, data_lector):
        product_update, product_new = data_lector
        msg = ""
        flag, error, result, msg_update = self.update_products(product_update)
        msg += msg_update
        flag, error, result, msg_create = self.create_new_products(product_new)
        msg += msg_create
        create_notification_permission_notGUI(
            msg,
            ["almacen"],
            "Actualizacion de inventario",
            0,
            0,
        )
        self.update_table()

    def on_click_table_item(self, event):
        item = event.widget.item(event.widget.selection()[0])
        locations = json.loads(item["values"][10])
        codes = json.loads(item["values"][9])
        try:
            loc_1 = locations["location_1"]
            loc_2 = locations["location_2"]
        except Exception as e:
            print("bad structure: ", e)
            loc_1 = ""
            loc_2 = ""
        data = item["values"][0:-2] + [str(codes), loc_1, loc_2]
        self.clear_fields()
        self.entries[0].configure(state="normal")
        for entry, value in zip(self.entries, data):
            if isinstance(entry, ttk.Combobox):
                entry.configure(state="normal")
                entry.set(value)
                entry.configure(state="readonly")
            elif isinstance(entry, ttk.IntVar):
                entry.set(value)
            elif isinstance(entry, ttk.Entry):
                entry.insert(0, value)
        self.entries[0].configure(state="disabled")
        self.id_to_modify = int(data[0])
        self.old_stock = float(data[4])

    def update_table(self, ignore_triger=False):
        self._products = fetch_products()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._products)
        if not ignore_triger:
            event = {
                "action": "update",
                "frames": ["Movimientos", "Inicio"],
                "sender": "Inventario",
            }
            self._trigger_actions_main_callback(**event)

    def get_inputs_valus(self):
        data = []
        for entry in self.entries:
            if isinstance(entry, ttk.Combobox):
                data.append(entry.get())
            elif isinstance(entry, ttk.IntVar):
                data.append(entry.get())
            elif isinstance(entry, ttk.Entry):
                data.append(entry.get())
        is_tool = data[7]
        is_internal = data[8]
        locations = {"location_1": data[10], "location_2": data[11]}
        codes = json.loads(data[9]) if data[9] != "" else []
        return (
            int(data[0]) if data[0] != "" else "",
            data[1],
            data[2],
            data[3],
            data[4],
            data[5],
            data[6],
            is_tool,
            is_internal,
            codes,
            locations,
        )

    def update_product(self):
        (
            product_id,
            product_sku,
            product_name,
            product_price,
            new_stock,
            product_category,
            product_supplier,
            is_tool,
            is_internal,
            codes,
            locations,
        ) = self.get_inputs_valus()
        flag, error, n_rows = update_product_db(
            product_id,
            product_sku,
            product_name,
            product_price,
            new_stock,
            self._categories_dict[product_category]
            if product_category != "None"
            else None,
            self._providers_dict_amc[product_supplier]
            if product_supplier != "None"
            else None,
            is_tool,
            is_internal,
            codes,
            locations,
        )
        if not flag:
            msg = f"Error al actualizar producto: {product_sku}--{product_id}"
        else:
            msg = f"Producto actualizado: {product_sku}--{product_id}"
            quantity_moved = float(new_stock) - self.old_stock
            movement = "entrada" if quantity_moved > 0 else "salida"
            date = datetime.now().strftime(format_date)
            flag, error, result = create_in_movement_db(
                product_id, movement, abs(quantity_moved), date, None
            )
            if not flag:
                msg += (
                    f"\nError al crear movimiento: {product_sku}--{product_id}--{error}"
                )
            else:
                msg += f"\nMovimiento creado: {product_sku}--{product_id}--{result}"
        msg_not = "System Notification\n" + msg
        create_notification_permission_notGUI(
            msg_not,
            ["almacen"],
            "Actualización de producto",
            0,
            0,
        )
        self.clear_fields()
        self.update_table()

    def clear_fields(self):
        self.entries[0].configure(state="normal")
        for index, entry in enumerate(self.entries):
            if isinstance(entry, ttk.Combobox):
                entry.configure(state="normal")
                entry.set("None")
                entry.configure(state="readonly")
            elif isinstance(entry, ttk.IntVar):
                entry.set(0)
            elif isinstance(entry, ttk.Entry):
                entry.delete(0, "end")
        self.id_to_modify = None
        self.old_stock = None
        self.entries[0].configure(state="disabled")

    def add_product(self):
        (
            product_id,
            product_sku,
            product_name,
            product_price,
            product_stock,
            product_category,
            product_supplier,
            is_tool,
            is_internal,
            codes,
            locations,
        ) = self.get_inputs_valus()
        if (
            product_sku == ""
            or product_name == ""
            or product_price == ""
            or product_stock == ""
            or int(product_stock) <= 0
            or product_category == ""
            or product_supplier == ""
        ):
            print("Error, values must not be empty.")
            return

        if product_id != "":
            print("Error, product id must be empty.")
            return
        flag, error, lastrowid = create_product_db(
            product_sku,
            product_name,
            product_price,
            product_stock,
            self._categories_dict[product_category]
            if product_category != "None"
            else None,
            self._providers_dict_amc[product_supplier]
            if product_supplier != "None"
            else None,
            is_tool,
            is_internal,
            codes,
            locations,
        )
        if not flag:
            msg = f"Error al crear producto: {product_sku}--{lastrowid}--{error}"
        else:
            msg = f"Producto creado: {product_sku}--id: {lastrowid}"
            movement = "entrada"
            date = datetime.now().strftime(format_date)
            quantity = product_stock
            flag, error, result = create_in_movement_db(
                product_id, movement, quantity, date, None
            )
            if not flag:
                msg += (
                    f"\nError al crear movimiento: {product_sku}--{lastrowid}--{error}"
                )
            else:
                msg += f"\nMovimiento creado: {product_sku}--{lastrowid}"
        msg_not = "System Notification\n" + msg
        create_notification_permission_notGUI(
            msg_not,
            ["almacen"],
            "Creación de producto",
            0,
            0,
        )
        self.clear_fields()
        self.update_table()

    def delete_product(self):
        product_id = self.entries[0].get()
        if product_id == "":
            return
        flag, error, result = delete_product_db(product_id)
        if not flag:
            msg = f"Error al eliminar producto: {product_id}"
        else:
            msg = f"Producto eliminado: {product_id}"
        create_notification_permission_notGUI(
            msg,
            ["almacen"],
            "Eliminación de producto",
            0,
            0,
        )
        self.clear_fields()
        self.update_table()

    def update_products(self, products_data):
        flag, error, result = update_multiple_row_products_amc(
            products_data, self._categories_dict, self._providers_dict_amc
        )
        msg = (
            "Inventario actualizado"
            if flag
            else f"Error al actualizar inventario: {str(error)}"
        )
        if not flag:
            return flag, error, result, msg
        # generate data movements from stock value
        date = datetime.now().strftime(format_date)
        data_movements = []
        for item in products_data:
            if int(item[4]) - int(item[-1]) == 0:
                continue
            elif int(item[4]) - int(item[-1]) < 0:
                data_movements.append(
                    [item[0], "salida", abs(int(item[4]) - int(item[-1])), date, "None"]
                )
            else:
                data_movements.append(
                    [item[0], "entrada", int(item[4]) - int(item[-1]), date, "None"]
                )
        if len(data_movements) != 0:
            flag, error, result = insert_multiple_row_movements_amc(
                tuple(data_movements)
            )
            msg += (
                "\nMovimientos registrados"
                if flag
                else f"\nError al registrar movimientos: {str(error)}"
            )
        create_notification_permission_notGUI(
            msg,
            ["almacen"],
            "Actualizacion de inventario",
            0,
            0,
        )
        return flag, error, result, msg

    def create_new_products(self, products_new_data):
        result = 0
        flag, error, lastrow_id = insert_multiple_row_products_amc(
            products_new_data, self._categories_dict, self._providers_dict_amc
        )
        msg = "Productos creados" if flag else f"Error al crear productos: {str(error)}"
        if not flag:
            print("error at insert multiple: ", flag, error, lastrow_id)
            return flag, error, lastrow_id, msg
        # generate data movements from stock value
        date = datetime.now().strftime(format_date)
        new_ids = range(lastrow_id - len(products_new_data) + 1, lastrow_id + 1)
        data_movements = []
        for index, item in enumerate(products_new_data):
            if int(item[4]) == 0:
                continue
            data_movements.append(
                [new_ids[index], "entrada", int(item[4]), date, "None"]
            )
        if len(data_movements) != 0:
            flag, error, result = insert_multiple_row_movements_amc(
                tuple(data_movements)
            )
            msg += (
                "\nMovimientos registrados"
                if flag
                else f"\nError al registrar movimientos: {str(error)}"
            )
        create_notification_permission_notGUI(
            msg,
            ["almacen"],
            "Actualizacion de inventario",
            0,
            0,
        )
        return flag, error, result, msg

    def update_procedure(self, **events):
        self.update_table(ignore_triger=True)
