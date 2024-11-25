# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 04/nov/2024  at 15:12 $"

import json
from tkinter import filedialog

import fitz
import ttkbootstrap as ttk
from PIL import Image, ImageTk
from reportlab.lib.units import mm
from ttkbootstrap.dialogs import Messagebox
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
from templates.forms.BarCodeGenerator import create_one_code
from templates.modules.Almacen.Frame_Movements import fetch_all_products
from templates.modules.Almacen.SubFrameBarcodeMultiple import BarcodeMultipleFrame


def generate_default_configuration_barcodes(**kwargs):
    title_offset = kwargs.get("title_offset", "0, 0")
    title_offset = (
        (float(title_offset.split(", ")[0]), float(title_offset.split(", ")[1]))
        if len(title_offset.split(", ")) != 2
        else (0, 0)
    )
    code_offset = kwargs.get("code_offset", "0, 0")
    code_offset = (
        (float(code_offset.split(", ")[0]), float(code_offset.split(", ")[1]))
        if len(code_offset.split(", ")) != 2
        else (0, 0)
    )
    sku_offset = kwargs.get("sku_offset", "0, 0")
    sku_offset = (
        (float(sku_offset.split(", ")[0]), float(sku_offset.split(", ")[1]))
        if len(sku_offset.split(", ")) != 2
        else (0, 0)
    )
    name_offset = kwargs.get("name_offset", "0, 0")
    name_offset = (
        (float(name_offset.split(", ")[0]), float(name_offset.split(", ")[1]))
        if len(name_offset.split(", ")) != 2
        else (0, 0)
    )
    codebar_size = kwargs.get("codebar_size", "0.4, 20")
    codebar_size = (
        (float(codebar_size.split(", ")[0]), float(codebar_size.split(", ")[1]))
        if len(codebar_size.split(", ")) != 2
        else (0.4, 20)
    )
    codebar_offset = kwargs.get("codebar_offset", "0, -7")
    codebar_offset = (
        (float(codebar_offset.split(", ")[0]), float(codebar_offset.split(", ")[1]))
        if len(codebar_offset.split(", ")) != 2
        else (0, -7)
    )
    kw = {
        "title": kwargs.get("title", "Titulo de prueba"),
        "title_font": kwargs.get("title_font", 14),
        "title_offset": (title_offset[0] * mm, title_offset[1] * mm),
        "code": kwargs.get("code", "A123456789"),
        "code_font": kwargs.get("code_font", 7),
        "code_offset": (code_offset[0] * mm, code_offset[1] * mm),
        "sku": kwargs.get("sku", "SKU123456789"),
        "sku_font": kwargs.get("sku_font", 6),
        "sku_offset": (sku_offset[0] * mm, sku_offset[1] * mm),
        "name": kwargs.get("name", "Producto de prueba"),
        "name_font": kwargs.get("name_font", 9),
        "name_offset": (name_offset[0] * mm, name_offset[1] * mm),
        "name_width": kwargs.get("name_limit", 20),
        "type_code": kwargs.get("type_code", "128"),
        "width_bars": codebar_size[0] * mm,
        "height_bars": codebar_size[1] * mm,
        "codebar_offset": (codebar_offset[0] * mm, codebar_offset[1] * mm),
        "pagesize": kwargs.get("pagesize", "default"),
        "orientation": kwargs.get("orientation", "horizontal"),
        "border_on": kwargs.get("border", True),
        "filepath": kwargs.get("filepath", file_codebar),
    }
    # noinspection PyTypeChecker
    values = (
        kw["title"],
        kw["title_font"],
        ", ".join(map(str, title_offset)),
        kw["code"],
        kw["code_font"],
        ", ".join(map(str, code_offset)),
        kw["sku"],
        kw["sku_font"],
        ", ".join(map(str, sku_offset)),
        kw["name"],
        kw["name_font"],
        ", ".join(map(str, name_offset)),
        kw["name_width"],
        kw["type_code"],
        ", ".join(map(str, codebar_size)),
        ", ".join(map(str, codebar_offset)),
        kw["pagesize"],
        kw["orientation"],
        kw["border_on"],
        kw["filepath"],
    )
    return kw, values


def create_input_widgets(master):
    create_label(master, text="Título: ", row=0, column=0, sticky="w")
    create_label(master, text="Letra título: ", row=2, column=0, sticky="w")
    create_label(master, text="Offset título: ", row=4, column=0, sticky="w")
    create_label(master, text="Codigo: ", row=0, column=1, sticky="w")
    create_label(master, text="Letra código: ", row=2, column=1, sticky="w")
    create_label(master, text="Offset código: ", row=4, column=1, sticky="w")
    create_label(master, text="SKU: ", row=0, column=2, sticky="w")
    create_label(master, text="Letra SKU: ", row=2, column=2, sticky="w")
    create_label(master, text="Offset SKU: ", row=4, column=2, sticky="w")
    create_label(master, text="Descripcion: ", row=0, column=3, sticky="w")
    create_label(master, text="Letra Descripción: ", row=2, column=3, sticky="w")
    create_label(master, text="Offset Descripción: ", row=4, column=3, sticky="w")
    create_label(master, text="Limite descripción: ", row=6, column=3, sticky="w")
    create_label(master, text="Tipo de Codigo: ", row=0, column=4, sticky="w")
    create_label(master, text="Tamaño: ", row=2, column=4, sticky="w")
    create_label(master, text="Offset Codigo de Barras: ", row=4, column=4, sticky="w")
    create_label(master, text="Tamaño de página: ", row=0, column=5, sticky="w")
    create_label(master, text="Orientación: ", row=2, column=5, sticky="w")
    create_label(master, text="Bordes: ", row=4, column=5, sticky="w")
    create_label(master, text="Ruta: ", row=6, column=5, sticky="w")
    # inputs
    input_title = create_entry(master, row=1, column=0, sticky="nswe")
    input_title_font = create_entry(master, row=3, column=0, sticky="nswe")
    input_title_offset = create_entry(master, row=5, column=0, sticky="nswe")
    input_code = create_entry(master, row=1, column=1, sticky="nswe")
    input_code_font = create_entry(master, row=3, column=1, sticky="nswe")
    input_code_offset = create_entry(master, row=5, column=1, sticky="nswe")
    input_sku = create_entry(master, row=1, column=2, sticky="nswe")
    input_sku_font = create_entry(master, row=3, column=2, sticky="nswe")
    input_sku_offset = create_entry(master, row=5, column=2, sticky="nswe")
    input_description = create_entry(master, row=1, column=3, sticky="nswe")
    input_description_font = create_entry(master, row=3, column=3, sticky="nswe")
    input_description_offset = create_entry(master, row=5, column=3, sticky="nswe")
    input_description_limit = create_entry(master, row=7, column=3, sticky="nswe")
    values = ["39", "39std", "93", "128", "usps", "eanbc8", "eanbc13", "qr"]
    input_type_code = create_Combobox(
        master, row=1, column=4, sticky="nswe", values=values
    )
    input_size_code = create_entry(master, row=3, column=4, sticky="nswe")
    input_offset_code = create_entry(master, row=5, column=4, sticky="nswe")
    input_size_page = create_Combobox(
        master, row=1, column=5, sticky="nswe", values=["default", "A4", "A5"]
    )
    input_orientation = create_Combobox(
        master, row=3, column=5, sticky="nswe", values=["horizontal", "vertical"]
    )
    input_border = create_Combobox(
        master, row=5, column=5, sticky="nswe", values=[True, False]
    )
    svar_title = ttk.StringVar(value=file_codebar)
    create_entry(
        master,
        textvariable=svar_title,
        row=7,
        column=5,
        sticky="nswe",
        state="readonly",
    )
    return (
        input_title,
        input_title_font,
        input_title_offset,
        input_code,
        input_code_font,
        input_code_offset,
        input_sku,
        input_sku_font,
        input_sku_offset,
        input_description,
        input_description_font,
        input_description_offset,
        input_description_limit,
        input_type_code,
        input_size_code,
        input_offset_code,
        input_size_page,
        input_orientation,
        input_border,
        svar_title,
    )


def create_input_widgets_multiple(master):
    create_label(master, text="Título: ", row=0, column=0, sticky="w")
    create_label(master, text="Letra título: ", row=2, column=0, sticky="w")
    create_label(master, text="Offset título: ", row=4, column=0, sticky="w")
    create_label(master, text="Codigo: ", row=0, column=1, sticky="w")
    create_label(master, text="Letra código: ", row=2, column=1, sticky="w")
    create_label(master, text="Offset código: ", row=4, column=1, sticky="w")
    create_label(master, text="SKU: ", row=0, column=2, sticky="w")
    create_label(master, text="Letra SKU: ", row=2, column=2, sticky="w")
    create_label(master, text="Offset SKU: ", row=4, column=2, sticky="w")
    create_label(master, text="Descripcion: ", row=0, column=3, sticky="w")
    create_label(master, text="Letra Descripción: ", row=2, column=3, sticky="w")
    create_label(master, text="Offset Descripción: ", row=4, column=3, sticky="w")
    create_label(master, text="Limite descripción: ", row=6, column=3, sticky="w")
    create_label(master, text="Tipo de Codigo: ", row=0, column=4, sticky="w")
    create_label(master, text="Tamaño: ", row=2, column=4, sticky="w")
    create_label(master, text="Offset Codigo de Barras: ", row=4, column=4, sticky="w")
    create_label(master, text="Tamaño de página: ", row=0, column=5, sticky="w")
    create_label(master, text="Orientación: ", row=2, column=5, sticky="w")
    create_label(master, text="Bordes: ", row=4, column=5, sticky="w")
    create_label(master, text="Ruta: ", row=6, column=5, sticky="w")
    # inputs
    input_title = create_entry(master, row=1, column=0, sticky="nswe")
    input_title_font = create_entry(master, row=3, column=0, sticky="nswe")
    input_title_offset = create_entry(master, row=5, column=0, sticky="nswe")
    input_code = create_entry(master, row=1, column=1, sticky="nswe")
    input_code_font = create_entry(master, row=3, column=1, sticky="nswe")
    input_code_offset = create_entry(master, row=5, column=1, sticky="nswe")
    input_sku = create_entry(master, row=1, column=2, sticky="nswe")
    input_sku_font = create_entry(master, row=3, column=2, sticky="nswe")
    input_sku_offset = create_entry(master, row=5, column=2, sticky="nswe")
    input_description = create_entry(master, row=1, column=3, sticky="nswe")
    input_description_font = create_entry(master, row=3, column=3, sticky="nswe")
    input_description_offset = create_entry(master, row=5, column=3, sticky="nswe")
    input_description_limit = create_entry(master, row=7, column=3, sticky="nswe")
    values = ["39", "39std", "93", "128", "usps", "eanbc8", "eanbc13", "qr"]
    input_type_code = create_Combobox(
        master, row=1, column=4, sticky="nswe", values=values
    )
    input_size_code = create_entry(master, row=3, column=4, sticky="nswe")
    input_offset_code = create_entry(master, row=5, column=4, sticky="nswe")
    input_size_page = create_Combobox(
        master, row=1, column=5, sticky="nswe", values=["default", "A4", "A5"]
    )
    input_orientation = create_Combobox(
        master, row=3, column=5, sticky="nswe", values=["horizontal", "vertical"]
    )
    input_border = create_Combobox(
        master, row=5, column=5, sticky="nswe", values=[True, False]
    )
    svar_title = ttk.StringVar(value=file_codebar)
    create_entry(
        master,
        textvariable=svar_title,
        row=7,
        column=5,
        sticky="nswe",
        state="readonly",
    )
    return (
        input_title,
        input_title_font,
        input_title_offset,
        input_code,
        input_code_font,
        input_code_offset,
        input_sku,
        input_sku_font,
        input_sku_offset,
        input_description,
        input_description_font,
        input_description_offset,
        input_description_limit,
        input_type_code,
        input_size_code,
        input_offset_code,
        input_size_page,
        input_orientation,
        input_border,
        svar_title,
    )


def create_btns(master, callbacks):
    create_button(
        master,
        row=0,
        column=0,
        text="Actualizar",
        command=callbacks.get("update", None),
        style="primary",
    )
    create_button(
        master,
        row=0,
        column=1,
        text="Limpiar",
        command=callbacks.get("clear", None),
        style="warning",
    )
    create_button(
        master,
        row=0,
        column=2,
        text="Guardar",
        command=callbacks.get("path", None),
        style="info",
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


def generate_kw_for_barcode(values, **kwargs):
    temp = {
        "title": kwargs.get("title", values[0]),
        "title_font": kwargs.get("title_font", values[1]),
        "title_offset": kwargs.get("title_offset", values[2]),
        "code": kwargs.get("code", values[3]),
        "code_font": kwargs.get("code_font", values[4]),
        "code_offset": kwargs.get("code_offset", values[5]),
        "sku": kwargs.get("sku", values[6]),
        "sku_font": kwargs.get("sku_font", values[7]),
        "sku_offset": kwargs.get("sku_offset", values[8]),
        "name": kwargs.get("name", values[9]),
        "name_font": kwargs.get("name_font", values[10]),
        "name_offset": kwargs.get("name_offset", values[11]),
        "name_limit": kwargs.get("name_limit", values[12]),
        "type_code": kwargs.get("type_code", values[13]),
        "codebar_size": kwargs.get("codebar_size", values[14]),
        "codebar_offset": kwargs.get("codebar_offset", values[15]),
        "pagesize": kwargs.get("pagesize", values[16]),
        "orientation": kwargs.get("orientation", values[17]),
        "border": kwargs.get("border", values[18]),
        "filepath": kwargs.get("filepath", values[19]),
    }
    kw, values = generate_default_configuration_barcodes(**temp)
    return kw





class BarcodeFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.kw = None
        self.title_pdf = "Telintec-Almacen"
        self.id_to_generate = None
        self.columnconfigure(0, weight=1)
        self.barcode_image = None
        self.canvas = None
        self.barcode = kwargs.get("code", "None")
        self.sku = kwargs.get("sku", "None")
        self.name = kwargs.get("name", "None")
        self.pdf_barcode = kwargs.get("pdf_filepath", file_codebar)

        # ------------------------------title-----------------------------------------
        create_label(
            self, 0, 0, text="Vista previa", font=("Helvetica", 20), sticky="we"
        )
        # ------------------------------barcode----------------------------------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, sticky="nswe")
        frame_inputs.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.entries = create_input_widgets(frame_inputs)
        kw, values = generate_default_configuration_barcodes(
            code=self.barcode,
            sku=self.sku,
            name=self.name,
            filepath=self.pdf_barcode,
            title=self.title_pdf,
        )
        set_values_entries(self.entries, values)
        # ------------------------------canvas-----------------------------------------
        self.frame_canvas = ttk.Frame(self)
        self.frame_canvas.grid(row=2, column=0, sticky="n")
        self.frame_canvas.columnconfigure(0, weight=1)
        self.frame_canvas.rowconfigure(0, weight=1)
        self.create_canvas()
        # ------------------------------btns-------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=3, column=0, sticky="nswe")
        frame_btns.columnconfigure((0, 1, 2, 3), weight=1)
        create_btns(
            frame_btns,
            {
                "update": self.update_barcode,
                "clear": self.clear_btn_action,
                "path": self.select_path,
            },
        )
        # ------------------------------table-------------------------------------------
        frame_table = ttk.Frame(self)
        frame_table.grid(row=4, column=0, sticky="nswe")
        frame_table.columnconfigure(0, weight=1)
        from templates.modules.Almacen.Inventory import coldata_inventory

        self.table = create_table(
            frame_table,
            coldata_inventory,
            fetch_all_products(),
            self.on_double_click,
        )

    def create_canvas(self):
        pdf_document = fitz.open(self.pdf_barcode)
        page = pdf_document.load_page(0)  # Load the first page
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        if self.canvas is not None:
            self.canvas.destroy()
        self.barcode_image = ImageTk.PhotoImage(image)
        page_size = get_page_size(self.entries[-4].get())
        self.canvas = ttk.Canvas(
            self.frame_canvas, width=page_size[1] * mm, height=page_size[0] * mm
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.create_image(
            page_size[1] * mm / 2, page_size[0] * mm / 2, image=self.barcode_image
        )

    def on_double_click(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        self.id_to_generate = int(row[0])
        extra_codes = json.loads(row[9])
        self.kw, values = generate_default_configuration_barcodes(
            code=row[1],
            sku=extra_codes[0] if len(extra_codes) > 0 else "None",
            name=row[2],
            filepath=self.pdf_barcode,
            title=self.title_pdf,
        )
        self.clear_fields()
        set_values_entries(self.entries, values)

    def update_barcode(self):
        if self.id_to_generate is None:
            Messagebox.show_error("No se ha seleccionado un producto", "Error")
            return
        values = get_entries_values(self.entries)
        self.kw = generate_kw_for_barcode(values)
        create_one_code(**self.kw)
        self.create_canvas()

    def clear_fields(self):
        for index, entry in enumerate(self.entries):
            if isinstance(entry, ttk.Combobox):
                entry.configure(state="normal")
                entry.set("None")
                entry.configure(state="readonly")
            elif isinstance(entry, ttk.IntVar):
                entry.set(0)
            elif isinstance(entry, ttk.Entry):
                entry.delete(0, "end")

    def clear_btn_action(self):
        self.id_to_generate = None
        self.barcode = "None"
        self.sku = "None"
        self.name = "None"
        kw, values = generate_default_configuration_barcodes(
            code=self.barcode,
            sku=self.sku,
            name=self.name,
            filepath=self.pdf_barcode,
            title=self.title_pdf,
        )
        set_values_entries(self.entries, values)
        self.clear_fields()
        set_values_entries(self.entries, values)

    def select_path(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Guardar como",
        )
        if not filepath:
            return
        self.pdf_barcode = filepath
