# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 04/nov/2024  at 15:12 $"

import fitz
import ttkbootstrap as ttk
from PIL import Image, ImageTk

from templates.Functions_GUI_Utils import create_button, create_label


class BarcodeFrame(ttk.Toplevel):
    def __init__(self, master, barcode, **kwargs):
        super().__init__(master)
        self.barcode_image = None
        self.canvas = None
        self.title("Código de barras")
        self.geometry("300x500")
        self.resizable(True, True)
        self.barcode = barcode
        self.pdf_barcode = kwargs.get("pdf_filepath", None)
        pdf_document = fitz.open(self.pdf_barcode)
        page = pdf_document.load_page(0)  # Load the first page
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        self.barcode_image = ImageTk.PhotoImage(image)
        # ------------------------------title-----------------------------------------
        create_label(
            self, 0, 0, text="Vista previa", font=("Helvetica", 20), sticky="we"
        )
        # ------------------------------canvas-----------------------------------------
        frame_canvas = ttk.Frame(self)
        frame_canvas.grid(row=1, column=0, sticky="n")
        self.canvas = ttk.Canvas(frame_canvas, width=300, height=300)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.create_image(150, 150, image=self.barcode_image)
        # ------------------------------btns-------------------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=2, column=0, sticky="nswe")
        create_button(
            frame_btns, 0, 1, text="Imprimir Codigo", command=self.print_barcode
        )

    def print_barcode(self):
        print(self.pdf_barcode)
