# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 04/nov/2024  at 15:12 $"

import fitz
import ttkbootstrap as ttk
from PIL import Image, ImageTk

from templates.Functions_GUI_Utils import create_button


class BarcodeFrame(ttk.Toplevel):
    def __init__(self, master, barcode, **kwargs):
        super().__init__(master)
        self.barcode_image = None
        self.canvas = None
        self.title("Código de barras")
        self.geometry("300x300")
        self.resizable(False, False)
        self.barcode = barcode
        self.pdf_barcode = kwargs.get("pdf_filepath", None)
        self.create_widgets()

    def create_widgets(self):
        # read pdf file
        if self.pdf_barcode is None:
            self.destroy()
            return
        pdf_document = fitz.open(self.pdf_barcode)
        page = pdf_document.load_page(0)  # Load the first page
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        self.barcode_image = ImageTk.PhotoImage(image)
        frame_canvas = ttk.Frame(self)
        frame_canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas = ttk.Canvas(frame_canvas, width=300, height=300)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.create_image(150, 150, image=self.barcode_image)
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=1, column=0, sticky="nswe")
        create_button(self, 0, 1, text="Imprimir Codigo", command=self.print_barcode)

    def print_barcode(self):
        print(self.pdf_barcode)
