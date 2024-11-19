# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 04/nov/2024  at 15:12 $"

import fitz
import ttkbootstrap as ttk
from PIL import Image, ImageTk
from reportlab.lib.units import mm
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tableview import Tableview

from static.constants import file_codebar
from templates.Functions_GUI_Utils import (
    create_button,
    create_label,
    create_entry,
    create_Combobox,
)
from templates.Functions_Utils import get_page_size
from templates.modules.Almacen.Frame_Movements import fetch_all_products


def create_input_widgets(master, data):
    create_label(master, text="Titulo: ", row=0, column=0, sticky="w")
    create_label(master, text="Codigo: ", row=1, column=0, sticky="w")
    create_label(master, text="SKU: ", row=2, column=0, sticky="w")
    create_label(master, text="Descripcion: ", row=3, column=0, sticky="w")
    create_label(master, text="Tipo de Codigo: ", row=4, column=0, sticky="w")
    # inputs
    input_title = create_entry(master, row=0, column=1, sticky="nswe")
    input_code = create_entry(master, row=1, column=1, sticky="nswe")
    input_sku = create_entry(master, row=2, column=1, sticky="nswe")
    input_description = create_entry(master, row=3, column=1, sticky="nswe")
    values = ["39", "39std", "93", "128", "usps", "eanbc8", "eanbc13", "qr"]
    input_type_code = create_Combobox(
        master, row=4, column=1, sticky="nswe", values=values
    )
    return input_title, input_code, input_sku, input_description, input_type_code


def create_btns(master, callbacks):
    create_button(
        master,
        row=0,
        column=0,
        text="Actualizar",
        command=callbacks["update"],
        style="primary",
    )
    create_button(
        master,
        row=0,
        column=1,
        text="Generar Codigo",
        command=callbacks["print"],
        style="success",
    )


def create_table(master, coldata, row_data, callback):
    table = Tableview(
        master,
        coldata=coldata,
        autofit=True,
        paginated=True,
        searchable=True,
        rowdata=row_data,
        height=15,
    )
    table.grid(row=1, column=0, sticky="nswe", padx=(5, 30))
    table.view.bind("<Double-1>", callback)
    columns_header = table.get_columns()
    for item in columns_header:
        if item.headertext in ["Completado", "Actualizado"]:
            item.hide()
    return table


def update_table(table):
    data = fetch_all_products()
    row_data, coldata = (data.get("data", []), data.get("columns", []))
    if len(row_data) == 0 or len(coldata) == 0 or len(row_data[0]) != len(coldata):
        print("No hay datos para actualizar. Error....")
        return None
    table.unload_table_data()
    table.build_table_data(coldata, row_data)
    columns_header = table.get_columns()
    for item in columns_header:
        if item.headertext in ["Completado", "Actualizado"]:
            item.hide()


def get_entries_values(entries):
    values = []
    for entry in entries:
        if isinstance(entry, ttk.Combobox):
            values.append(entry.get())
        elif isinstance(entry, ttk.StringVar):
            values.append(entry.get())
        elif isinstance(entry, ttk.Entry):
            values.append(entry.get())
        else:
            values.append(None)
    return values


def set_values_entries(entries, values):
    for index, entry in enumerate(entries):
        if isinstance(entry, ttk.Combobox):
            entry.set(values[index])
        elif isinstance(entry, ttk.StringVar):
            entry.set(values[index])
        elif isinstance(entry, ttk.Entry):
            entry.delete(0, "end")
            entry.insert(0, values[index])


class BarcodeSubFrameSelector(ttk.Toplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.title("Código de barras")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        frame_notebook = ScrolledFrame(self, autohide=True)
        frame_notebook.grid(row=0, column=0, sticky="nswe")
        frame_notebook.columnconfigure(0, weight=1)
        nb = ttk.Notebook(frame_notebook)
        nb.grid(row=0, column=0, sticky="nswe", padx=(5, 20), pady=5)
        nb.columnconfigure(0, weight=1)
        frame_individual = BarcodeFrame(nb, **kwargs)
        nb.add(frame_individual, text="Individual")
        frame_multiple = BarcodeFrame(nb, **kwargs)
        nb.add(frame_multiple, text="Multiple")


class BarcodeFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.barcode_image = None
        self.canvas = None
        self.barcode = kwargs.get("code", "None")
        self.pdf_barcode = kwargs.get("pdf_filepath", file_codebar)
        pdf_document = fitz.open(self.pdf_barcode)
        page = pdf_document.load_page(0)  # Load the first page
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        self.barcode_image = ImageTk.PhotoImage(image)
        # ------------------------------title-----------------------------------------
        create_label(
            self, 0, 0, text="Vista previa", font=("Helvetica", 20), sticky="we"
        )
        # ------------------------------barcode----------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        # ------------------------------canvas-----------------------------------------
        frame_canvas = ttk.Frame(self)
        frame_canvas.grid(row=2, column=0, sticky="n")
        frame_canvas.columnconfigure(0, weight=1)
        frame_canvas.rowconfigure(0, weight=1)
        page_size = get_page_size("default")
        self.canvas = ttk.Canvas(
            frame_canvas, width=page_size[1] * mm, height=page_size[0] * mm
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.create_image(
            page_size[1] * mm / 2, page_size[0] * mm / 2, image=self.barcode_image
        )
        # ------------------------------table-------------------------------------------
        frame_table = ttk.Frame(self)
        frame_table.grid(row=3, column=0, sticky="nswe")
        frame_table.columnconfigure(0, weight=1)
        from templates.modules.Almacen.Inventory import coldata_inventory

        self.table = create_table(
            frame_table,
            coldata_inventory,
            fetch_all_products(),
            self.on_double_click,
        )
        # ------------------------------btns-------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=4, column=0, sticky="nswe")
        frame_btns.columnconfigure((0, 1), weight=1)
        create_btns(
            frame_btns, {"update": self.print_barcode, "print": self.print_barcode}
        )

    def on_double_click(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        print(row)

    def update_barcode(self):
        print("barcode")

    def print_barcode(self):
        print(self.pdf_barcode)
        # create_BarCodeFormat(sku, sku, name, filepath, "128")
