# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 25/nov/2024  at 15:54 $"

from tkinter import filedialog

import fitz
import ttkbootstrap as ttk
from PIL import Image, ImageTk
from reportlab.lib.units import mm
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
from templates.resources.methods.Aux_Inventory import generate_kw_for_barcode, generate_default_configuration_barcodes, coldata_inventory


def create_input_widgets(master):
    create_label(master, text="Título: ", row=0, column=0, sticky="w")
    create_label(master, text="Letra título: ", row=2, column=0, sticky="w")
    create_label(master, text="Offset título: ", row=4, column=0, sticky="w")
    create_label(master, text="Letra código: ", row=6, column=0, sticky="w")
    create_label(master, text="Offset código: ", row=8, column=0, sticky="w")
    create_label(master, text="Letra SKU: ", row=0, column=1, sticky="w")
    create_label(master, text="Offset SKU: ", row=2, column=1, sticky="w")
    create_label(master, text="Letra Descripción: ", row=4, column=1, sticky="w")
    create_label(master, text="Offset Descripción: ", row=6, column=1, sticky="w")
    create_label(master, text="Limite descripción: ", row=8, column=1, sticky="w")
    create_label(master, text="Tipo de Codigo: ", row=0, column=2, sticky="w")
    create_label(master, text="Tamaño: ", row=2, column=2, sticky="w")
    create_label(master, text="Offset Codigo de Barras: ", row=4, column=2, sticky="w")
    create_label(master, text="Tamaño de página: ", row=6, column=2, sticky="w")
    create_label(master, text="Orientación: ", row=8, column=2, sticky="w")
    create_label(master, text="Bordes: ", row=0, column=3, sticky="w")
    create_label(master, text="Ruta: ", row=2, column=3, sticky="w")
    create_label(master, text="Productos: ", row=4, column=3, sticky="w")
    create_label(master, text="Rango[1,3-4]: ", row=6, column=3, sticky="w")
    # inputs
    input_title = create_entry(master, row=1, column=0, sticky="nswe")
    input_title_font = create_entry(master, row=3, column=0, sticky="nswe")
    input_title_offset = create_entry(master, row=5, column=0, sticky="nswe")
    input_code_font = create_entry(master, row=7, column=0, sticky="nswe")
    input_code_offset = create_entry(master, row=9, column=0, sticky="nswe")
    input_sku_font = create_entry(master, row=1, column=1, sticky="nswe")
    input_sku_offset = create_entry(master, row=3, column=1, sticky="nswe")
    input_description_font = create_entry(master, row=5, column=1, sticky="nswe")
    input_description_offset = create_entry(master, row=7, column=1, sticky="nswe")
    input_description_limit = create_entry(master, row=9, column=1, sticky="nswe")
    values = ["39", "39std", "93", "128", "usps", "eanbc8", "eanbc13", "qr"]
    input_type_code = create_Combobox(
        master, row=1, column=2, sticky="nswe", values=values
    )
    input_size_code = create_entry(master, row=3, column=2, sticky="nswe")
    input_offset_code = create_entry(master, row=5, column=2, sticky="nswe")
    input_size_page = create_Combobox(
        master, row=7, column=2, sticky="nswe", values=["default", "A4", "A5"]
    )
    input_orientation = create_Combobox(
        master, row=9, column=2, sticky="nswe", values=["horizontal", "vertical"]
    )
    input_border = create_Combobox(
        master, row=1, column=3, sticky="nswe", values=[True, False]
    )
    svar_title = ttk.StringVar(value=file_codebar)
    create_entry(
        master,
        textvariable=svar_title,
        row=3,
        column=3,
        sticky="nswe",
        state="readonly",
    )
    values_lista = ["Todos", "Personalizado"]
    input_lista = create_Combobox(
        master,
        row=5,
        column=3,
        sticky="nswe",
        values=values_lista,
        state="readonly",
    )
    input_custom = create_entry(master, row=7, column=3, sticky="nswe")
    return (
        input_title,
        input_title_font,
        input_title_offset,
        input_code_font,
        input_code_offset,
        input_sku_font,
        input_sku_offset,
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
        input_lista,
        input_custom,
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
        text="Generar Codigo",
        command=callbacks.get("print", None),
        style="success",
    )
    create_button(
        master,
        row=0,
        column=2,
        text="Limpiar",
        command=callbacks.get("clear", None),
        style="warning",
    )
    create_button(
        master,
        row=0,
        column=3,
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


class BarcodeMultipleFrame(ttk.Frame):
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
        # exclude 3, 6, 9
        new_values = [
            item for index, item in enumerate(values) if index not in [3, 6, 9]
        ] + ["Todos", "1"]
        set_values_entries(self.entries, new_values)
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
                "print": self.print_barcode,
                "clear": self.clear_btn_action,
                "path": self.select_path,
            },
        )
        # ------------------------------table-------------------------------------------
        frame_table = ttk.Frame(self)
        frame_table.grid(row=4, column=0, sticky="nswe")
        frame_table.columnconfigure(0, weight=1)
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
        page_size = get_page_size(self.entries[-6].get())
        self.canvas = ttk.Canvas(
            self.frame_canvas, width=page_size[1] * mm, height=page_size[0] * mm
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.create_image(
            page_size[1] * mm / 2, page_size[0] * mm / 2, image=self.barcode_image
        )

    def on_double_click(self, event):
        row = event.widget.item(event.widget.selection()[0], "values")
        list_ids = self.entries[-1].get().split(",")
        list_selection = self.entries[-2].get()
        if list_selection != "Todos":
            print(row[0])
            if row[0] not in list_ids:
                list_ids.append(row[0])
            else:
                list_ids.remove(row[0])
            self.entries[-1].delete(0, "end")
            self.entries[-1].insert(0, ",".join(list_ids))

    def update_barcode(self):
        values = get_entries_values(self.entries)
        new_values = (
            values[0:3]
            + ["new name example"]
            + values[3:6]
            + ["new code example"]
            + values[6:9]
            + ["new sku example"]
            + values[9:-2]
        )
        self.kw = generate_kw_for_barcode(new_values)
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
        new_values = [
            item for index, item in enumerate(values) if index not in [3, 6, 9]
        ] + ["Todos", "1"]
        self.clear_fields()
        print(new_values)
        set_values_entries(self.entries, new_values)

    def select_path(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Guardar como",
        )
        if not filepath:
            return
        self.pdf_barcode = filepath

    def print_barcode(self):
        list_ids = self.entries[-1].get().replace(" ", "").split(",")
        list_selection = self.entries[-2].get()
        if list_selection == "Todos":
            print("Todos")
        else:
            ids = []
            for item in list_ids:
                print(item)
                if "-" in item:
                    start, end = map(int, item.split("-"))
                    ids.extend(range(start, end + 1))
                else:
                    ids.append(int(item))
            print(ids)
