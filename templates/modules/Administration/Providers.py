import time

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from static.constants import log_file_db
from templates.Functions_GUI_Utils import (
    create_label,
    create_entry,
    create_Combobox,
    create_button,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.product.p_and_s_controller import get_all_suppliers
from templates.controllers.supplier.suppliers_controller import (
    create_supplier_amc,
    update_supplier_amc,
    delete_supplier_amc,
)
from templates.misc.Functions_Files import write_log_file


def fetch_all_providers():
    flag, error, data = get_all_suppliers()
    if not flag:
        print(error)
        return []
    return data


def create_widgets_input(master):
    create_label(
        master,
        text="Agregar nuevo proveedor",
        font=("Arial", 20),
        row=0,
        column=0,
        sticky="w",
        columnspan=4,
    )
    # Inputs left
    create_label(master, text="ID Cliente", row=1, column=0)
    create_label(master, text="Nombre", row=2, column=0)
    create_label(master, text="Vendedor", row=3, column=0)
    create_label(master, text="Email", row=4, column=0)
    create_label(master, text="Telefono", row=1, column=2)
    create_label(master, text="Dirección", row=2, column=2)
    create_label(master, text="Pagina Web", row=3, column=2)
    create_label(master, text="Tipo", row=4, column=2)
    id_p = create_entry(master, row=1, column=1, sticky="nswe")
    name = create_entry(master, row=2, column=1, sticky="nswe")
    seller = create_entry(master, row=3, column=1, sticky="nswe")
    email = create_entry(master, row=4, column=1, sticky="nswe")
    phone = create_entry(master, row=1, column=3, sticky="nswe")
    address = create_entry(master, row=2, column=3, sticky="nswe")
    web = create_entry(master, row=3, column=3, sticky="nswe")
    values = ["materiales", "EPP", "linea"]
    type_c = create_Combobox(master, row=4, column=3, sticky="nswe", values=values)
    id_p.configure(state="disabled")
    return id_p, name, seller, email, phone, address, web, type_c


class ProvidersScreen(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.id_to_modify = None
        self.table = None
        self.col_data = None
        self.master = master
        self.columnconfigure(0, weight=1)
        self._suppliers = (
            fetch_all_providers()
            if "data_providers_gen" not in kwargs["data"]
            else kwargs["data"]["data_providers_gen"]
        )
        self.usernamedata = kwargs.get("username_data", None)
        # -----------------------------------------Ttile--------------------------------------------
        create_label(
            self,
            text="Proveedores",
            font=("Arial Black", 25),
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=10,
        )
        # -----------------------------------------Table--------------------------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=0, sticky="nswe")
        self.frame_table.columnconfigure(0, weight=1)
        self.create_table()
        # -----------------------------------------Inputs--------------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=2, column=0, sticky="nswe")
        frame_inputs.columnconfigure((0, 1, 2, 3), weight=1)
        self.entries = create_widgets_input(frame_inputs)
        #  -----------------------------------------btns--------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=3, column=0, sticky="nswe")
        frame_btns.columnconfigure((0, 1, 2, 3), weight=1)
        self.create_btns(frame_btns)

    def create_btns(self, master):
        create_button(
            master,
            text="Agregar Cliente",
            command=self.create_provider,
            row=0,
            column=0,
        )
        create_button(
            master,
            text="Actualizar Cliente",
            command=self.update_provider,
            row=0,
            column=1,
        )
        create_button(
            master,
            text="Eliminar Cliente",
            command=self.delete_provider,
            row=0,
            column=2,
        )
        create_button(
            master, text="Limpiar Campos", command=self.clear_fields, row=0, column=3
        )

    def update_table(self):
        """Updates the table of providers"""
        self._suppliers = fetch_all_providers()
        self.table.unload_table_data()
        time.sleep(0.5)
        self.table.build_table_data(self.col_data, self._suppliers)
        self.table.autofit_columns()

    def clear_fields(self):
        self.entries[0].configure(state="normal")
        for item in self.entries:
            if isinstance(item, ttk.Combobox):
                item.set("None")
            elif isinstance(item, ttk.Entry):
                item.delete(0, "end")
        self.entries[0].configure(state="readonly")

    def get_entries_values(self):
        self.entries[0].configure(state="normal")
        data = [item.get() for item in self.entries]
        self.entries[0].configure(state="readonly")
        return data

    def create_provider(self):
        data = self.get_entries_values()
        flag, error, lastrowid = create_supplier_amc(
            data[1], data[2], data[3], data[4], data[5], data[6], data[7]
        )
        if not flag:
            msg = f"Error al crear proveedor: {str(error)}"
        else:
            msg = f"Proveedor creado: {data[1]}--id: {lastrowid} por el usuario: {self.usernamedata['id']}"
            self.update_table()
            self.clear_fields()
        self.end_action_db(msg, "Proveedor creado.")

    def update_provider(self):
        data = self.get_entries_values()
        flag, error, result = update_supplier_amc(
            data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]
        )
        if not flag:
            msg = f"Error al actualizar proveedor: {str(error)}"
        else:
            msg = f"Proveedor actualizado: {data[1]}--id: {data[0]} por el usuario: {self.usernamedata['id']}"
            self.update_table()
            self.clear_fields()
        self.end_action_db(msg, "Proveedor actualizado.")

    def delete_provider(self):
        if self.id_to_modify is None:
            print("No hay cliente seleccionado")
            return
        flag, error, result = delete_supplier_amc(self.id_to_modify)
        if not flag:
            msg = f"Error al eliminar proveedor: {str(error)}"
        else:
            msg = f"Proveedor eliminado: {self.id_to_modify} por el usuario: {self.usernamedata['id']}"
            self.update_table()
            self.clear_fields()
        self.end_action_db(msg, "Proveedor eliminado.")

    def create_table(self):
        create_label(
            self.frame_table,
            text="Tabla de proveedores",
            font=("Arial", 16),
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=10,
        )
        self.col_data = [
            {"text": "ID Proveedor", "stretch": True},
            {"text": "Nombre", "stretch": True},
            {"text": "Vendedor", "stretch": True},
            {"text": "Email", "stretch": True},
            {"text": "Telefono", "stretch": True},
            {"text": "Direccion", "stretch": True},
            {"text": "Pagina Web", "stretch": True},
            {"text": "Tipo", "stretch": True},
        ]
        if self.table is not None:
            self.table.destroy()
        self.table = Tableview(
            master=self.frame_table,
            paginated=True,
            pagesize=10,
            searchable=True,
            autofit=True,
        )
        try:
            self.table.build_table_data(self.col_data, self._suppliers)
            self.table.grid(row=1, column=0, sticky="nswe", padx=15, pady=5)
            self.table.view.bind("<Double-1>", self.on_double_click_table)
        except Exception as e:
            print("Error at creating table: ", e)

    def on_double_click_table(self, event):
        data = event.widget.item(event.widget.selection()[0])["values"]
        self.id_to_modify = int(data[0])
        self.entries[0].configure(state="normal")
        for i, item in enumerate(self.entries):
            if isinstance(item, ttk.Combobox):
                item.set(data[i])
            elif isinstance(item, ttk.Entry):
                item.delete(0, "end")
                item.insert(0, data[i])
        self.entries[0].configure(state="readonly")

    def end_action_db(self, msg, title):
        if msg is None or msg == "":
            return
        create_notification_permission_notGUI(
            msg, ["Administracion"], title, self.usernamedata["id"], 0
        )
        write_log_file(log_file_db, msg)
