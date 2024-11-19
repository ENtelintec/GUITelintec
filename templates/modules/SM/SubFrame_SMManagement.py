# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 15/abr./2024  at 9:41 $"

import json
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tableview import Tableview

from static.constants import status_dic
from templates.misc.Functions_AuxFiles import get_all_sm_entries, get_all_sm_products
from templates.resources.midleware.Functions_DB_midleware import (
    dispatch_products,
    update_data_dicts,
)
from templates.Functions_GUI_Utils import (
    create_label,
    create_button,
    create_entry,
    create_notification_permission,
)
from templates.controllers.employees.employees_controller import get_sm_employees
from templates.controllers.material_request.sm_controller import (
    update_history_sm,
    cancel_sm_db,
)


def reorder_data_table(data):
    columns = [
        "Estado",
        "ID",
        "Folio",
        "Contrato",
        "Planta",
        "Ubicación",
        "Cliente",
        "Empleado",
        "Orden/Cotización",
        "Fecha",
        "Fecha Limite",
        "Items",
        "Historial",
        "Comentario",
        "Destinos",
    ]
    new_data = []
    for row in data:
        for index, objectss in enumerate(row):
            (
                id_sm,
                folio,
                contract,
                plant,
                location,
                client,
                employee,
                order,
                date,
                date_limit,
                items,
                status,
                history,
                comment,
                destinations,
            ) = row
        new_data.append(
            (
                status,
                id_sm,
                folio,
                contract,
                plant,
                location,
                client,
                employee,
                order,
                date,
                date_limit,
                items,
                history,
                comment,
                destinations,
            )
        )

    return new_data, columns


def load_data(is_super=False, emp_id=None):
    data_sm, columns_sm = get_all_sm_entries(
        filter_status=False, is_supper=True, emp_id=emp_id
    )
    data_sm_not_supper = []
    products, columns_products = get_all_sm_products()
    flag, error, employees = get_sm_employees()
    if not is_super:
        data_sm_not_supper = [data for data in data_sm if data[7] == emp_id]
    data_dic = {
        "data_sm": data_sm,
        "columns_sm": columns_sm,
        "data_sm_not_supper": data_sm_not_supper,
        "products": products,
        "employees": employees,
    }
    return data_dic


class SMManagement(ttk.Frame):
    def __init__(self, master, data_emp=None, **kwargs):
        super().__init__(master)
        self.emp_creation = None
        self.columnconfigure(1, weight=1)
        # -----------------------Variables-----------------------
        self.data_emp = (
            data_emp if data_emp is not None else {"id": 60, "name": "Default"}
        )
        data_dic = load_data(True, self.data_emp["id"])
        self._id_emp = self.data_emp["id"]
        self.data_sm = None
        self.products = data_dic["products"]
        self.employees = data_dic["employees"]
        self.style_gui = kwargs["style_gui"]
        self._id_sm_to_edit = None
        self.status_sm = None
        self.svar_info = ttk.StringVar(value="")
        self.svar_entry_comment = ttk.StringVar(value="")
        self.history_sm = None
        self.products_sm = None
        self.table_events = None
        # -----------------------Title---------------------------
        create_label(
            self,
            0,
            0,
            text="Procesado de las material_request",
            font=("Helvetica", 26, "bold"),
            columnspan=2,
        )
        # -----------------------Frames---------------------------
        self.frame_table = ttk.Frame(self)
        self.frame_table.grid(row=1, column=1, padx=20, pady=10)
        self.frame_table.columnconfigure(0, weight=1)
        self.frame_resumen = ttk.Frame(self)
        self.frame_resumen.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_btns = ttk.Frame(self)
        self.frame_btns.grid(
            row=2, column=0, padx=10, pady=10, sticky="nswe", columnspan=2
        )
        self.frame_btns.columnconfigure((0, 1, 2), weight=1)
        # -----------------------Table---------------------------
        self.table_events = self.create_table(self.frame_table, data_dic["data_sm"])
        self.info_products, self.info_history = self.create_resumen_widgets(
            self.frame_resumen
        )
        self.create_buttons(self.frame_btns)

    def create_table(self, master, data=None, re_order=True):
        self.table_events.destroy() if self.table_events is not None else None
        columns = [
            "Estado",
            "ID",
            "Codigo",
            "Folio",
            "Contrato",
            "Planta",
            "Ubicación",
            "Cliente",
            "Empleado",
            "Orden/Cotización",
            "Fecha",
            "Fecha Limite",
            "Items",
            "Historial",
            "Comentario",
        ]
        if data is None:
            self.data_sm, columns = get_all_sm_entries(is_supper=True)
        else:
            self.data_sm = data
        if re_order:
            self.data_sm, columns = reorder_data_table(self.data_sm)
        table = Tableview(
            master,
            coldata=columns,
            rowdata=self.data_sm,
            paginated=True,
            searchable=True,
            autofit=True,
            height=21,
            pagesize=20,
        )
        table.grid(row=0, column=0, padx=10, pady=10)
        table.view.bind("<Double-1>", self.on_double_click_table)
        return table

    def create_buttons(self, master):
        create_label(master, 0, 0, text="Comentario: ", font=("Helvetica", 16, "bold"))
        create_entry(master, 50, 0, 1, textvariable=self.svar_entry_comment)
        create_label(
            master,
            1,
            0,
            textvariable=self.svar_info,
            font=("Helvetica", 16, "bold"),
            columnspan=3,
        )
        create_button(
            master,
            2,
            0,
            "Despachar",
            command=self.on_dispatch_click,
            sticky="n",
            width=15,
            bootstyle="success",
        )
        create_button(
            master,
            2,
            1,
            "Actualizar",
            command=self.on_update_table_click,
            sticky="n",
            width=15,
            bootstyle="normal",
        )
        create_button(
            master,
            2,
            2,
            "Cancelar",
            command=self.on_cancel_click,
            sticky="n",
            width=15,
            bootstyle="danger",
        )

    def create_resumen_widgets(self, master):
        create_label(
            master,
            0,
            0,
            text="Resumen",
            font=("Helvetica", 20, "bold"),
            columnspan=2,
            sticky="n",
        )
        create_label(
            master,
            1,
            0,
            text="Productos material_request: ",
            font=("Helvetica", 16, "bold"),
        )
        create_label(
            master,
            3,
            0,
            text="Historial material_request: ",
            font=("Helvetica", 16, "bold"),
        )
        info_products = ScrolledText(master, padding=5, height=10, autohide=True)
        info_products.grid(row=2, column=0, padx=5, pady=10, sticky="nswe")
        info_history = ScrolledText(master, padding=5, height=10, autohide=True)
        info_history.grid(row=4, column=0, padx=5, pady=10, sticky="nswe")
        return info_products, info_history

    def on_dispatch_click(self):
        if self._id_sm_to_edit is None or self.status_sm is None:
            return
        if self.status_sm == "Completado" or self.status_sm == "Finalizado":
            self.svar_info.set("La material_request ya esta completada")
            return
        self.history_sm.append(
            {
                "user": self.data_emp["id"],
                "event": "dispatch",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "comment": self.svar_entry_comment.get(),
            }
        )
        products_to_dispacth = []
        products_to_request = []
        new_products = []
        for item in self.products_sm:
            if "(Nuevo)" in item["comment"] and "(Pedido)" not in item["comment"]:
                new_products.append(item)
                continue
            if (
                item["stock"] >= item["quantity"] or "(Pedido)" in item["comment"]
            ) and "(Despachado)" not in item["comment"]:
                products_to_dispacth.append(item)
            elif (
                "(Pedido)" not in item["comment"]
                and "(Despachado)" not in item["comment"]
            ):
                products_to_request.append(item)
        msg = f"Esta por despachar la material_request con ID-{self._id_sm_to_edit}.\n Esta seguro de esto?"
        msg += "\n\nProductos a despachar: "
        for item in products_to_dispacth:
            msg += f"\n{item['name']} - {item['quantity']}"
        msg += "\n\nProductos a pedir: "
        for item in products_to_request:
            msg += f"\n{item['name']} - {item['quantity']}"
        msg += "\n\nProductos nuevos: "
        for item in new_products:
            msg += f"\n{item['name']} - {item['quantity']}"
        answer = Messagebox.show_question(title="Confirmacion", message=msg)
        if answer == "No":
            return
        # update db with corresponding movements
        (products_to_dispacth, products_to_request, new_products) = dispatch_products(
            products_to_dispacth, products_to_request, self._id_sm_to_edit, new_products
        )
        # update table with new stock
        self.products_sm = update_data_dicts(
            [products_to_dispacth, products_to_request, new_products], self.products_sm
        )
        is_complete = (
            True if len(products_to_request) == 0 and len(new_products) == 0 else False
        )
        flag, error, result = update_history_sm(
            self._id_sm_to_edit, self.history_sm, self.products_sm, is_complete
        )
        if flag:
            self.svar_info.set(
                f"material_request con ID-{self._id_sm_to_edit} despachada"
            )
            self.update_table("dispatch", 2) if len(products_to_request) == 0 and len(
                new_products
            ) == 0 else self.update_table("dispatch", 1)
            msg = f"SM con ID-{self._id_sm_to_edit} despachada"
            create_notification_permission(
                msg, ["sm"], "SM Despachada", self._id_emp, self.emp_creation
            )
        else:
            self.svar_info.set(
                f"Error al despachar material_request con ID-{self._id_sm_to_edit}"
            )

    def on_update_table_click(self):
        self.clean_widgets()
        self.table_events = self.create_table(self.frame_table)

    def on_cancel_click(self):
        if self._id_sm_to_edit is None:
            self.svar_info.set("No se ha seleccionado ninguna material_request")
            return
        msg = f"Esta por cancelar la material_request con ID-{self._id_sm_to_edit}.\n Esta seguro de esto?"
        answer = Messagebox.show_question(title="Confirmacion", message=msg)
        if answer == "No":
            return
        self.history_sm.append(
            {
                "user": self.data_emp["id"],
                "event": "cancelation",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        flag, error, result = cancel_sm_db(self._id_sm_to_edit, self.history_sm)
        if flag:
            msg = f"SM con ID-{self._id_sm_to_edit} cancelada"
            self.update_table("cancel")
            self.clean_widgets()
            self.svar_info.set(msg)
            create_notification_permission(
                msg, ["sm"], "SM Cancelada", self._id_emp, self.emp_creation
            )

    def on_double_click_table(self, event):
        self.clean_widgets()
        row = event.widget.item(event.widget.selection()[0], "values")
        try:
            self._id_sm_to_edit = int(row[1])
        except ValueError:
            self._id_sm_to_edit = None
            print("Value error: ", row[1])
        if self._id_sm_to_edit is None:
            print("Error en la base de datos")
            return
        self.status_sm = row[0]
        self.emp_creation = int(row[8])
        self.products_sm = json.loads(row[12])
        for i, item in enumerate(self.products_sm):
            for product in self.products:
                if item["id"] == product[0]:
                    self.info_products.text.insert(
                        ttk.END, f"{i + 1}. Producto: ", "property"
                    )
                    self.info_products.text.insert(
                        ttk.END, f"{product[3]}\n", "description"
                    )
                    self.info_products.text.insert(
                        ttk.END, " Cantidad requerida: ", "property"
                    )
                    self.info_products.text.insert(
                        ttk.END, f"{item['quantity']}\n", "description"
                    )
                    self.info_products.text.insert(
                        ttk.END, " Cantidad disponible: ", "property"
                    )
                    self.info_products.text.insert(
                        ttk.END, f"{product[2]}\n", "description"
                    )
                    self.info_products.text.insert(ttk.END, " UDM: ", "property")
                    self.info_products.text.insert(
                        ttk.END, f"{product[1]}\n", "description"
                    )
                    self.info_products.text.insert(ttk.END, " Comentario: ", "property")
                    comment = item["comment"]
                    tag_name = "description"
                    if "(Nuevo)" in comment:
                        tag_name = "nuevo"
                    if "(Pedido)" in comment:
                        tag_name = "pedido"
                    if "(Despachado)" in comment:
                        tag_name = "despachado"
                    self.info_products.text.insert(ttk.END, f"{comment}\n", tag_name)
                    item["stock"] = product[2]
                    item["name"] = product[3]
                    self.products_sm[i] = item
                    break
        self.info_products.text.tag_config(
            "property", foreground=self.style_gui.colors.get("warning")
        )
        self.info_products.text.tag_config(
            "nuevo", foreground=self.style_gui.colors.get("danger")
        )
        self.info_products.text.tag_config(
            "description", foreground=self.style_gui.colors.get("fg")
        )
        self.info_products.text.tag_config(
            "pedido", foreground=self.style_gui.colors.get("secondary")
        )
        self.info_products.text.tag_config(
            "despachado", foreground=self.style_gui.colors.get("success")
        )
        self.history_sm = json.loads(row[13])
        emp_found = False
        for i, event in enumerate(self.history_sm):
            for employee in self.employees:
                if event["user"] == employee[0]:
                    self.info_history.text.insert(
                        ttk.END, f"{i + 1}. Evento: ", "property"
                    )
                    self.info_history.text.insert(
                        ttk.END, f"{event['event']}\n", "description"
                    )
                    self.info_history.text.insert(ttk.END, " Empleado: ", "property")
                    self.info_history.text.insert(
                        ttk.END,
                        f"{employee[1].title()} {employee[2].title()}\n",
                        "description",
                    )
                    self.info_history.text.insert(ttk.END, " Fecha: ", "property")
                    self.info_history.text.insert(
                        ttk.END, f"{event['date']}\n", "description"
                    )
                    if "comment" in event.keys():
                        self.info_history.text.insert(
                            ttk.END, " Comentario: ", "property"
                        )
                        self.info_history.text.insert(
                            ttk.END, f"{event['comment']}\n", "description"
                        )
                    emp_found = True
                    break
            if not emp_found:
                self.info_history.text.insert(ttk.END, f"{i + 1}. Evento: ", "property")
                self.info_history.text.insert(
                    ttk.END, f"{event['event']}\n", "description"
                )
                self.info_history.text.insert(ttk.END, " Empleado: ", "property")
                self.info_history.text.insert(
                    ttk.END, f"{event['user']}\n", "description"
                )
                self.info_history.text.insert(ttk.END, " Fecha: ", "property")
                self.info_history.text.insert(
                    ttk.END, f"{event['date']}\n", "description"
                )
        self.info_history.text.tag_config(
            "property", foreground=self.style_gui.colors.get("warning")
        )
        self.info_history.text.tag_config(
            "description", foreground=self.style_gui.colors.get("fg")
        )

    def clean_widgets(self):
        self.info_products.text.delete("1.0", "end")
        self.info_history.text.delete("1.0", "end")
        self.svar_entry_comment.set("")
        # self.svar_info.set("Seleccione una sm de la tabla")
        self._id_sm_to_edit = None

    def update_table(self, event, type_e=None):
        match event:
            case "cancel":
                data = []
                for item in self.data_sm:
                    if int(item[1]) != self._id_sm_to_edit:
                        data.append(item)
                    else:
                        (
                            status,
                            id_sm,
                            code,
                            folio,
                            contract,
                            plant,
                            location,
                            client,
                            employee,
                            order,
                            date,
                            date_limit,
                            items,
                            history,
                            comment,
                        ) = item
                        data.append(
                            (
                                "cancelado",
                                id_sm,
                                code,
                                folio,
                                contract,
                                plant,
                                location,
                                client,
                                employee,
                                order,
                                date,
                                date_limit,
                                json.dumps(self.products_sm),
                                json.dumps(self.history_sm),
                                comment,
                            )
                        )
                self.table_events = self.create_table(
                    self.frame_table, data, re_order=False
                )

            case "dispatch":
                data = []
                type_e = 1 if type_e is None else type_e
                for item in self.data_sm:
                    if int(item[1]) != self._id_sm_to_edit:
                        data.append(item)
                    else:
                        (
                            status,
                            id_sm,
                            code,
                            folio,
                            contract,
                            plant,
                            location,
                            client,
                            employee,
                            order,
                            date,
                            date_limit,
                            items,
                            history,
                            comment,
                        ) = item
                        data.append(
                            (
                                status_dic[type_e],
                                id_sm,
                                code,
                                folio,
                                contract,
                                plant,
                                location,
                                client,
                                employee,
                                order,
                                date,
                                date_limit,
                                json.dumps(self.products_sm),
                                json.dumps(self.history_sm),
                                comment,
                            )
                        )
                self.table_events = self.create_table(
                    self.frame_table, data, re_order=False
                )
                self.clean_widgets()
            case _:
                print("Error evento no permitido")
