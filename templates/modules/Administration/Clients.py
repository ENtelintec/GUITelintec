import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from static.extensions import log_file_db
from templates.Functions_GUI_Utils import (
    create_label,
    create_entry,
    create_button,
)
from templates.Functions_Utils import create_notification_permission_notGUI
from templates.controllers.customer.customers_controller import (
    get_all_customers_db,
    create_customer_db,
    update_customer_db,
    delete_customer_db,
)
from templates.misc.Functions_Files import write_log_file


def fetch_all_customers():
    flag, error, data = get_all_customers_db()
    if not flag:
        print(error)
        return []
    return data


def create_widgets_input(master):
    create_label(
        master,
        text="Agregar nuevo cliente",
        font=("Arial", 20),
        row=0,
        column=0,
        sticky="w",
        columnspan=4,
    )
    # Inputs left
    create_label(master, text="ID Cliente", row=1, column=0)
    create_label(master, text="Nombre", row=2, column=0)
    create_label(master, text="Email", row=3, column=0)
    create_label(master, text="Telefono", row=1, column=2)
    create_label(master, text="RFC", row=2, column=2)
    create_label(master, text="Dirección", row=3, column=2)
    id_p = create_entry(master, row=1, column=1, sticky="nswe")
    name = create_entry(master, row=2, column=1, sticky="nswe")
    email = create_entry(master, row=3, column=1, sticky="nswe")
    phone = create_entry(master, row=1, column=3, sticky="nswe")
    rfc = create_entry(master, row=2, column=3, sticky="nswe")
    address = create_entry(master, row=3, column=3, sticky="nswe")
    return id_p, name, email, phone, rfc, address


class ClientsScreen(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.id_to_modify = None
        self.usernamedata = kwargs.get("username_data", None)
        self.table = None
        self.col_data = None
        self.master = master
        self.columnconfigure(0, weight=1)
        self._clients = (
            fetch_all_customers()
            if "data_clients_gen" not in kwargs["data"]
            else kwargs["data"]["data_clients_gen"]
        )
        self._table = None
        # -----------------------------------------Ttile--------------------------------------------
        create_label(
            self,
            text="Clientes",
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
            master, text="Agregar Cliente", command=self.create_client, row=0, column=0
        )
        create_button(
            master,
            text="Actualizar Cliente",
            command=self.update_client,
            row=0,
            column=1,
        )
        create_button(
            master, text="Eliminar Cliente", command=self.delete_client, row=0, column=2
        )
        create_button(
            master, text="Limpiar Campos", command=self.clear_fields, row=0, column=3
        )

    def update_table(self):
        self._clients = fetch_all_customers()
        try:
            self.table.build_table_data(self.col_data, self._clients)
            self.table.autofit_columns()
        except Exception as e:
            print("Error at updating table: ", e)

    def clear_fields(self):
        self.entries[0].configure(state="normal")
        for item in self.entries:
            if isinstance(item, ttk.Combobox):
                item.set("None")
            elif isinstance(item, ttk.Entry):
                item.delete(0, "end")
        self.entries[0].configure(state="readonly")
        self.id_to_modify = None

    def get_entries_values(self):
        self.entries[0].configure(state="normal")
        data = [item.get() for item in self.entries]
        self.entries[0].configure(state="readonly")
        return data

    def create_client(self):
        data = self.get_entries_values()
        ""
        flag, error, lastrowid = create_customer_db(
            data[1], data[2], data[3], data[4], data[5]
        )
        if not flag:
            msg = f"Error al crear cliente: {str(error)}"
        else:
            msg = f"Cliente creado: {data[1]}--id: {lastrowid} por el usuario: {self.usernamedata['id']}"
            self.update_table()
            self.clear_fields()
        self.end_action_db(msg, "Cliente creado")

    def update_client(self):
        if self.id_to_modify is None:
            print("No hay cliente seleccionado")
            return
        data = self.get_entries_values()
        flag, error, result = update_customer_db(
            data[0], data[1], data[2], data[3], data[4], data[5]
        )
        if not flag:
            msg = f"Error al actualizar cliente: {str(error)}"
        else:
            msg = f"Cliente actualizado: {data[1]}--id: {data[0]} por el usuario: {self.usernamedata['id']}"
            self.update_table()
            self.clear_fields()
        self.end_action_db(msg,  "Cliente actualizado")

    def delete_client(self):
        if self.id_to_modify is None:
            print("No hay cliente seleccionado")
            return
        flag, error, result = delete_customer_db(self.id_to_modify)
        if not flag:
            msg = f"Error al eliminar cliente: {str(error)}"
        else:
            msg = f"Cliente eliminado: {self.id_to_modify} por el usuario: {self.usernamedata['id']}"
            self.update_table()
            self.clear_fields()
        self.end_action_db(msg,  "Cliente eliminado")

    def create_table(self):
        create_label(
            self.frame_table,
            text="Tabla de clientes",
            font=("Arial", 16),
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=10,
        )
        self.col_data = [
            {"text": "ID Cliente", "stretch": True},
            {"text": "Nombre", "stretch": True},
            {"text": "Email", "stretch": True},
            {"text": "Telefono", "stretch": True},
            {"text": "RFC", "stretch": True},
            {"text": "Direccion", "stretch": True},
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
            self.table.build_table_data(self.col_data, self._clients)
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
