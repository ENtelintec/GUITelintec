# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 01/may./2024  at 20:57 $'

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from templates.Funtions_Utils import create_widget_input_DB, create_btns_DB, create_visualizer_treeview, \
    set_entry_value
from templates.controllers.product.p_and_s_controller import insert_product_and_service, update_product_and_service, \
    delete_product_and_service


class ProductsFrame(ttk.Frame):
    def __init__(self, master, setting: dict = None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._id_product_update = None
        self.label = ttk.Label(self, text="Tabla de Servicios y Productos",
                               font=("Helvetica", 30, "bold"))
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # -----------------------subframe insert-----------------------
        self.insert_frame = ttk.Frame(self)
        self.insert_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.insert_frame.columnconfigure((0, 1, 2, 3), weight=1)
        # -----------------widgets on left_frame----------------------
        self.entries = create_widget_input_DB(
            self.insert_frame,
            "products",
        )
        # -----------------------insert button-----------------------
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=10, padx=10, sticky="nswe")
        btn_frame.columnconfigure((0, 1, 2), weight=1)
        self.btn_insert, self.btn_update, self.btn_delete = create_btns_DB(
            btn_frame,
            table_type=1,
            _command_insert=self._insert_product,
            _command_update=self._update_product,
            _command_delete=self._delete_product,
            width=20
        )
        # -----------------------subframe visual-----------------------
        self.visual_frame = ttk.Frame(self)
        self.visual_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        self.visual_frame.columnconfigure(0, weight=1)
        self.visual_frame.rowconfigure(0, weight=1)
        self.ps_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "p_and_s", row=0, column=0,
            style="success")
        self.ps_insert.view.bind("<Double-1>", self._get_data_product)

    def _insert_product(self):
        (name, model, brand, description, price_retail, stock, price_provider,
         support, service, categories, img_url, id_ps) = self.get_entries_values()
        id_ps = int(id_ps) if id_ps != "" else None
        support = int(support)
        service = int(service)
        if id_ps is None:
            return
        msg = (f"Are you sure you want to insert the following product:\n"
               f"Name: {name}\nModel: {model}\nBrand: {brand}\n"
               f"Description: {description}\nPrice retail: {price_retail}\n"
               f"Stock: {stock}\nPrice provider: {price_provider}\n"
               f"Support: {support}\nService: {service}\n"
               f"Categories: {categories}\nImg url: {img_url}\n"
               f"Id PS: {id_ps}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = insert_product_and_service(
            id_ps, name, model, brand, description, price_retail, stock,
            price_provider, support, service, categories, img_url)
        if flag:
            out = [id_ps, name, model, brand, description, price_retail, stock,
                   price_provider, support, service, categories, img_url]
            self.data.append(out)
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Product inserted")
            self.clean_widgets_products()
            self._id_product_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error inserting product:\n{e}")

    def _update_product(self):
        (name, model, brand, description, price_retail, stock, price_provider,
         support, service, categories, img_url, id_ps) = self.get_entries_values()
        id_ps = int(id_ps) if id_ps != "" else None
        support = int(support)
        service = int(service)
        if id_ps is None:
            return
        msg = (f"Are you sure you want to update the following product:\n"
               f"Name: {name}\nModel: {model}\nBrand: {brand}\n"
               f"Description: {description}\nPrice retail: {price_retail}\n"
               f"Stock: {stock}\nPrice provider: {price_provider}\n"
               f"Support: {support}\nService: {service}\n"
               f"Categories: {categories}\nImg url: {img_url}\n"
               f"Id PS: {id_ps}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = update_product_and_service(
            id_ps, name, model, brand, description, price_retail, stock,
            price_provider, support, service, categories, img_url)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_ps:
                    self.data[index] = [id_ps, name, model, brand, description, price_retail, stock,
                                        price_provider, support, service, categories, img_url]
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Product updated")
            self.clean_widgets_products()
            self._id_product_update = None

    def _delete_product(self):
        if self._id_product_update is None:
            return
        id_ps = self._id_product_update
        msg = (f"Are you sure you want to delete the following product:\n"
               f"Id PS: {id_ps}")
        answer = Messagebox.show_question(
            title="Confirmacion",
            message=msg
        )
        if answer == "No":
            return
        flag, e, out = delete_product_and_service(id_ps)
        if flag:
            for index, item in enumerate(self.data):
                if item[0] == id_ps:
                    self.data.pop(index)
                    break
            self._update_table_show(self.data)
            Messagebox.show_info(title="Informacion", message="Product deleted")
            self.clean_widgets_products()
            self._id_product_update = None
        else:
            Messagebox.show_error(title="Error", message=f"Error deleting product:\n{e}")
            return

    def _get_data_product(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self._id_product_update = int(row[0])
        set_entry_value(self.entries[0], row[1])
        set_entry_value(self.entries[1], row[2])
        set_entry_value(self.entries[2], row[3])
        set_entry_value(self.entries[3], row[4])
        set_entry_value(self.entries[4], row[5])
        set_entry_value(self.entries[5], row[6])
        set_entry_value(self.entries[6], row[7])
        self.entries[7].set(int(row[8]))
        self.entries[8].set(int(row[9]))
        set_entry_value(self.entries[9], row[10])
        set_entry_value(self.entries[10], row[11])
        set_entry_value(self.entries[11], row[0])

    def get_entries_values(self):
        out = []
        for item in self.entries:
            out.append(item.get())
        return out

    def clean_widgets_products(self):
        for index, item in self.entries:
            if index in [7, 8]:
                item.set(0)
            else:
                set_entry_value(item, "")

    def _update_table_show(self, data):
        self.ps_insert.destroy()
        self.ps_insert, self.data = create_visualizer_treeview(
            self.visual_frame, "p_and_s", row=0, column=0,
            style="success", data=data)
        self.ps_insert.view.bind("<Double-1>", self._get_data_product)
