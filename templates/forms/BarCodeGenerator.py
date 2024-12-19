# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 24/oct/2024  at 9:55 $"

from io import BytesIO

import fitz
from PIL import Image
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode import code93
from reportlab.graphics.barcode import code39, usps, usps4s, ecc200datamatrix
from reportlab.graphics.barcode import eanbc, qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from reportlab.platypus import Flowable

from static.constants import file_codebar
from templates.Functions_Utils import get_page_size
from templates.forms.PDFGenerator import wrap_text

data_company = {"name": "Telintec", "department": "Almacen"}


class VerticalText(Flowable):
    """Rotates a text."""

    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        c = self.canv
        c.rotate(90)
        fs = c._fontsize
        c.translate(1, -fs / 1.2)  # canvas._leading?
        c.drawString(0, 0, self.text)

    def wrap(self, aW, aH):
        canv = self.canv
        fn, fs = canv._fontname, canv._fontsize
        return canv._leading, 1 + canv.stringWidth(self.text, fn, fs)


def BarCode39(filepath, code, x, y, size):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)
    barcode39 = code39.Extended39(code)
    barcode39.drawOn(c, 1 * mm, 1 * mm)
    return barcode39


def BarCode39Std(filepath, code, x, y, size):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)

    barcode39 = code39.Standard39(code)

    barcode39.drawOn(c, 1 * mm, 1 * mm)
    return barcode39


def BarCode128(
    c,
    code,
    x,
    y,
    bar_height,
    bar_width,
):
    """
    Create barcode examples and embed in a PDF
    """
    barcode128 = code128.Code128(
        code,
        barHeight=bar_height,
        barWidth=bar_width,
    )
    width, height = (barcode128.width, barcode128.height)
    x_new = x - width / 2
    y_new = y - height / 2
    barcode128.drawOn(c, x_new, y_new)
    return barcode128


def BarCode93(filepath, code, x, y, size):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)
    barcode93 = code93.Standard93(code)
    barcode93.drawOn(c, 1 * mm, 9 * mm)
    # write code
    c.setFont("Helvetica", 8)
    c.drawString(1 * mm, 1 * mm, code)
    return barcode93


def BarCodeEANBC8(filepath, code, x, y, size):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)

    barcode_eanbc8 = eanbc.Ean8BarcodeWidget(code)
    # bounds = barcode_eanbc8.getBounds()
    # width = bounds[2] - bounds[0]
    # height = bounds[3] - bounds[1]
    d = Drawing(50, 10)
    d.add(barcode_eanbc8)
    renderPDF.draw(d, c, 11, 1)
    return barcode_eanbc8


def BarCodeEANBC13(filepath, code, x, y, size):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)

    barcode_eanbc13 = eanbc.Ean13BarcodeWidget(code)
    # bounds = barcode_eanbc13.getBounds()
    # width = bounds[2] - bounds[0]
    # height = bounds[3] - bounds[1]
    d = Drawing(50, 10)
    d.add(barcode_eanbc13)
    renderPDF.draw(d, c, 1, 1)
    return barcode_eanbc13


def BarCodeUsps(filepath, code, x, y, size):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)
    barcode_usps = usps.POSTNET(code)
    barcode_usps.drawOn(c, 1 * mm, 1 * mm)
    return barcode_usps


def BarcodeUsps4s(filepath, code, x, y, size):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)
    barcode_usps4s = usps4s.FIM(code)
    barcode_usps4s.drawOn(c, 1 * mm, 1 * mm)
    return barcode_usps4s


def BarCodeEcc200DataMatrix(filepath, code, x, y, size):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)
    barcode_ecc200datamatrix = ecc200datamatrix.DataMatrixWidget(code)
    # bounds = barcode_ecc200datamatrix.getBounds()
    # width = bounds[2] - bounds[0]
    # height = bounds[3] - bounds[1]
    d = Drawing(50, 50)
    d.add(barcode_ecc200datamatrix)
    renderPDF.draw(d, c, 1, 1)
    return barcode_ecc200datamatrix


def BarCodeQR(c, code, x, y, y_offset, width_q, height_q):
    """
    Create barcode examples and embed in a PDF
    """
    qr_code = qr.QrCodeWidget(str(code))
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(
        width_q, height_q, transform=[width_q / width, 0, 0, width_q / height, 0, 0]
    )
    d.add(qr_code)
    renderPDF.draw(d, c, x, y + y_offset)
    return qr_code


def draw_border(master_canvas, x, y, width, height, separation=(2, 2)):
    master_canvas.setLineWidth(1)
    master_canvas.rect(
        x + separation[0] / 2,
        y + separation[1] / 2,
        width - separation[0],
        height - separation[1],
    )


def draw_NameProduct(master_canvas, x, y, name_product, font_size=10):
    master_canvas.setFont("Helvetica", font_size)
    master_canvas.drawString(x, y, name_product)


def selectBarcodeType(
    master,
    type_code,
    code,
    pagesize,
    filepath="",
    **kwargs,
):
    match type_code:
        case "39":
            barcode = BarCode39(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "39std":
            barcode = BarCode39Std(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "93":
            barcode = BarCode93(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "128":
            barcode = BarCode128(
                master,
                code,
                kwargs.get("x", 0),
                kwargs.get("y", 0),
                kwargs.get("bar_height", 10 * mm),
                kwargs.get("bar_width", 0.5 * mm),
            )
        case "eanbc8":
            barcode = BarCodeEANBC8(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "eanbc13":
            barcode = BarCodeEANBC13(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "qr":
            # BarCodeQR(filepath, code_list[0], 0, 0, 0, width_q=40 * mm, height_q=40 * mm)
            x = kwargs.get("x", 0)
            y = kwargs.get("y", 0)
            width_q = kwargs.get("width_q", 40 * mm)
            height_q = kwargs.get("height_q", 40 * mm)
            y_offset = kwargs.get("y_offset", 0)
            barcode = BarCodeQR(master, code, x, y, y_offset, width_q, height_q)
        case _:
            barcode = None
            print("Error at creating barcode")
    return barcode


def create_BarCodeFormat(
    code, sku, name, filepath, type_code, pagesize="default", orientation="horizontal"
):
    pagesize = get_page_size(pagesize)
    pagesize = [pagesize[0] * mm, pagesize[1] * mm]
    pagesize = (pagesize[1], pagesize[0]) if orientation == "horizontal" else pagesize
    c = canvas.Canvas(filepath, pagesize=pagesize)
    draw_border(c, 0, 0, pagesize[0], pagesize[1])
    c.setFont("Helvetica", 14)
    c.drawCentredString(
        pagesize[0] / 2,
        pagesize[1] - 18,
        f"{data_company['name']}-{data_company['department']}",
    )
    name_list = wrap_text(name.upper(), pagesize[0] - 10 * mm).split("\n")
    font_name = 9
    c.setFont("Courier-Bold", font_name)
    for i, line in enumerate(name_list):
        c.drawString(5 * mm, pagesize[1] - 30 - i * font_name, line)
    c.setFont("Helvetica", 6)
    c.drawString(5 * mm, pagesize[1] - len(name_list) * font_name - 30, f"SKU: {sku}")
    barcode = selectBarcodeType(
        c, type_code, code, filepath=filepath, pagesize=pagesize
    )
    height_barcode = barcode.height if barcode else 10
    c.setFont("Helvetica", 7)
    c.drawCentredString(
        pagesize[0] / 2, pagesize[1] / 2 - 20 - height_barcode / 2 - 8, code
    )
    c.save()
    print("Barcode created: ", filepath)


def create_one_code(**kwargs):
    """
    Create one code with the following parameters:
        Example = {
            "title": "Titulo de prueba",
            "title_font": 14,
            "title_offset": (0 * mm, 0 * mm),
            "code": "A123456789",
            "code_font": 7,
            "code_offset": (0 * mm, 0 * mm),
            "sku": "SKU123456789",
            "sku_font": 6,
            "sku_offset": (0 * mm, 0 * mm),
            "name": "Producto de prueba de numero 2",
            "name_font": 9,
            "name_offset": (0 * mm, 0 * mm),
            "name_width": 20,
            "type_code": "128",
            "pagesize": "default",
            "orientation": "horizontal",
            "border": True,
            "filepath": "files/barcode.pdf",

            "offset_codebar": (0 * mm, -7 * mm),
            "width_bars": 40 * mm,
            "height_bars": 40 * mm,
        }
    :param kwargs:
    :return:
    """
    title = kwargs.get("title", "This is a product Title")
    title_font = int(kwargs.get("title_font", 14))
    title_offset = kwargs.get("title_offset", (0 * mm, 0 * mm))
    code = kwargs.get("code", "A123456789")
    font_code = int(kwargs.get("code_font", 7))
    code_offset = kwargs.get("code_offset", (0 * mm, 0 * mm))
    sku = kwargs.get("sku", "SKU123456789")
    sku_offset = kwargs.get("sku_offset", (0 * mm, 0 * mm))
    font_sku = int(kwargs.get("sku_font", 6))
    name = kwargs.get("name", "Producto de prueba de numero 2")
    font_name = int(kwargs.get("name_font", 9))
    pagesize = get_page_size(kwargs.get("pagesize", "default"))
    name_width = kwargs.get("name_width", pagesize[0] - 10 * mm)
    type_code = kwargs.get("type_code", "128")
    height_bars = kwargs.get("height_bars", 20 * mm)
    width_bars = kwargs.get("width_bars", 0.4 * mm)
    offset_codebar = kwargs.get("codebar_offset", (0 * mm, -7 * mm))
    orientation = kwargs.get("orientation", "horizontal")
    border_on = kwargs.get("border", True)
    filepath = kwargs.get("filepath", file_codebar)
    pagesize = [pagesize[0] * mm, pagesize[1] * mm]
    pagesize = (pagesize[1], pagesize[0]) if orientation == "horizontal" else pagesize
    # -------------------------------------create canvas-------------------------------------
    c = canvas.Canvas(filepath, pagesize=pagesize)
    # -------------------------------------create border-------------------------------------
    if border_on:
        draw_border(c, 0, 0, pagesize[0], pagesize[1])
    #  -------------------------------------create title-------------------------------------
    c.setFont("Helvetica", title_font)
    c.drawCentredString(
        pagesize[0] / 2 + title_offset[0],
        pagesize[1] - title_font * 1.5 + title_offset[1],
        title,
    )
    # -------------------------------------create name-------------------------------------
    name_list = wrap_text(name.upper(), name_width).split("\n")
    c.setFont("Courier-Bold", font_name)
    name_offset = kwargs.get("name_offset", (0 * mm, 0 * mm))
    for i, line in enumerate(name_list):
        c.drawString(
            5 * mm + name_offset[0],
            pagesize[1] - 32 - i * font_name + name_offset[1],
            line,
        )
    # -------------------------------------create sku-------------------------------------
    sku_position = (
        5 * mm + sku_offset[0],
        pagesize[1] - len(name_list) * font_name - 30 + sku_offset[1],
    )
    c.setFont("Helvetica", font_sku)
    c.drawString(sku_position[0], sku_position[1], f"SKU: {sku}")
    # -------------------------------------create barcode-------------------------------------
    x = pagesize[0] / 2 - offset_codebar[0]
    y = pagesize[1] / 2 - offset_codebar[1] - height_bars / 2
    kw = {
        "width_q": width_bars,
        "height_q": height_bars,
    }
    barcode = selectBarcodeType(
        c,
        type_code,
        code,
        filepath=filepath,
        pagesize=pagesize,
        x=x,
        y=y,
        bar_width=width_bars,
        bar_height=height_bars,
    )
    # -------------------------------------create code-------------------------------------
    c.setFont("Helvetica", font_code)
    height_barcode = barcode.height if barcode and type_code != "qr" else height_bars
    position_code = (
        pagesize[0] / 2 + code_offset[0],
        pagesize[1] / 2 - 20 - height_barcode / 2 - 8 + code_offset[1],
    )
    c.drawCentredString(position_code[0], position_code[1], code)
    c.save()
    print("Barcode created: ", filepath)


def create_multiple_barcodes_products(code_list, sku_list, name_list, **kwargs):
    """
    Create one code with the following parameters:
        Example = {
            "title": "Titulo de prueba",
            "title_font": 14,
            "title_offset": (0 * mm, 0 * mm),
            "code": "A123456789",
            "code_font": 7,
            "code_offset": (0 * mm, 0 * mm),
            "sku": "SKU123456789",
            "sku_font": 6,
            "sku_offset": (0 * mm, 0 * mm),
            "name": "Producto de prueba de numero 2",
            "name_font": 9,
            "name_offset": (0 * mm, 0 * mm),
            "name_width": 20,
            "type_code": "128",
            "pagesize": "default",
            "orientation": "horizontal",
            "border": True,
            "filepath": "files/barcode.pdf",

            "offset_codebar": (0 * mm, -7 * mm),
            "width_bars": 40 * mm,
            "height_bars": 40 * mm,
        }
    :param name_list:
    :param sku_list:
    :param code_list:
    :param kwargs:
    :return:
    """
    title_default = kwargs.get("title", "This is a product Title")
    title_font = int(kwargs.get("title_font", 14))
    title_offset = kwargs.get("title_offset", (0 * mm, 0 * mm))
    code_default = kwargs.get("code", "A123456789")
    font_code = int(kwargs.get("code_font", 7))
    code_offset = kwargs.get("code_offset", (0 * mm, 0 * mm))
    sku_default = kwargs.get("sku", "SKU123456789")
    sku_offset = kwargs.get("sku_offset", (0 * mm, 0 * mm))
    font_sku = int(kwargs.get("sku_font", 6))
    name_default = kwargs.get("name", "Producto de prueba de numero 2")
    font_name = int(kwargs.get("name_font", 9))
    pagesize = get_page_size(kwargs.get("pagesize", "default"))
    name_width = kwargs.get("name_limit", pagesize[0] - 10 * mm)
    type_code = kwargs.get("type_code", "128")
    height_bars = kwargs.get("height_bars", 20 * mm)
    width_bars = kwargs.get("width_bars", 0.4 * mm)
    offset_codebar = kwargs.get("codebar_offset", (0 * mm, -7 * mm))
    orientation = kwargs.get("orientation", "horizontal")
    border_on = kwargs.get("border", True)
    filepath = kwargs.get("filepath", file_codebar)
    pagesize = [pagesize[0] * mm, pagesize[1] * mm]
    pagesize = (pagesize[1], pagesize[0]) if orientation == "horizontal" else pagesize
    # -------------------------------------create canvas-------------------------------------
    c = canvas.Canvas(filepath, pagesize=pagesize)
    for name, code, sku in zip(name_list, code_list, sku_list):
        # -------------------------------------create border-------------------------------------
        if border_on:
            draw_border(c, 0, 0, pagesize[0], pagesize[1])
        #  -------------------------------------create title-------------------------------------
        c.setFont("Helvetica", title_font)
        c.drawCentredString(
            pagesize[0] / 2 + title_offset[0],
            pagesize[1] - title_font * 1.5 + title_offset[1],
            title_default,
        )
        # -------------------------------------create name-------------------------------------
        namelist = wrap_text(name.upper(), name_width).split("\n")
        c.setFont("Courier-Bold", font_name)
        for i, line in enumerate(namelist):
            c.drawString(5 * mm, pagesize[1] - 30 - i * font_name, line)
        # -------------------------------------create sku-------------------------------------
        sku_position = (
            5 * mm + sku_offset[0],
            pagesize[1] - len(namelist) * font_name - 30 + sku_offset[1],
        )
        c.setFont("Helvetica", font_sku)
        c.drawString(sku_position[0], sku_position[1], f"SKU: {sku}")
        # -------------------------------------create barcode-------------------------------------
        x = pagesize[0] / 2 - offset_codebar[0]
        y = pagesize[1] / 2 - offset_codebar[1] - height_bars / 2
        barcode = selectBarcodeType(
            c,
            type_code,
            code,
            filepath=filepath,
            pagesize=pagesize,
            x=x,
            y=y,
            bar_width=width_bars,
            bar_height=height_bars,
        )
        # -------------------------------------create code-------------------------------------
        c.setFont("Helvetica", font_code)
        height_barcode = barcode.height if barcode else 10
        position_code = (
            pagesize[0] / 2 + code_offset[0],
            pagesize[1] / 2 - 20 - height_barcode / 2 - 8 + code_offset[1],
        )
        c.drawCentredString(position_code[0], position_code[1], code)
        c.showPage()
    c.save()
    print("Barcodes created: ", filepath)


def create_multiple_barcodes(
    code_list,
    sku_list,
    name_list,
    filepath,
    type_code,
    pagesize="default",
    orientation="horizontal",
):
    pagesize = get_page_size(pagesize)
    pagesize = [pagesize[0] * mm, pagesize[1] * mm]
    pagesize = (pagesize[1], pagesize[0]) if orientation == "horizontal" else pagesize
    c = canvas.Canvas(filepath, pagesize=pagesize)
    for code, sku, name in zip(code_list, sku_list, name_list):
        draw_border(c, 0, 0, pagesize[0], pagesize[1])
        c.setFont("Helvetica", 14)
        c.drawCentredString(
            pagesize[0] / 2,
            pagesize[1] - 18,
            f"{data_company['name']}-{data_company['department']}",
        )
        name_list = wrap_text(name.upper(), pagesize[0] - 10 * mm).split("\n")
        font_name = 9
        c.setFont("Courier-Bold", font_name)
        for i, line in enumerate(name_list):
            c.drawString(5 * mm, pagesize[1] - 30 - i * font_name, line)
        c.setFont("Helvetica", 6)
        c.drawString(
            5 * mm, pagesize[1] - len(name_list) * font_name - 30, f"SKU: {sku}"
        )
        barcode = selectBarcodeType(
            c, type_code, code, filepath=filepath, pagesize=pagesize
        )
        height_barcode = barcode.height if barcode else 10
        c.setFont("Helvetica", 7)
        c.drawCentredString(
            pagesize[0] / 2,
            pagesize[1] / 2 - 20 - height_barcode / 2 - 8,
            text=str(code),
        )
        c.showPage()
    c.save()
    print("Barcodes created: ", filepath)


def create_two_code_one_page_multiple(
    code_list,
    sku_list,
    name_list,
    filepath,
    type_code,
    pagesize="default",
    orientation="vertical",
    height_barcode=10 * mm,
    width_barcode=0.40 * mm,
):
    pagesize_whole = get_page_size(pagesize)
    pagesize_whole = [
        pagesize_whole[0] * mm,
        pagesize_whole[1] * mm,
    ]
    pagesize_whole = (
        (pagesize_whole[1], pagesize_whole[0])
        if orientation == "horizontal"
        else pagesize_whole
    )
    c = canvas.Canvas(filepath, pagesize=pagesize_whole)
    code_per_page = 2
    counter = 0
    for code, sku, name in zip(code_list, sku_list, name_list):
        draw_border(
            c,
            0,
            pagesize_whole[1] / 2 - (pagesize_whole[1] / 2) * counter,
            pagesize_whole[0],
            pagesize_whole[1] / 2,
        )

        name_list = wrap_text(name.upper(), 25)
        name_list = name_list.split("\n")
        font_name = 8
        c.setFont("Courier-Bold", font_name)
        for i, line in enumerate(name_list[0:2]):
            c.drawString(
                2 * mm,
                pagesize_whole[1]
                - 3 * mm
                - (pagesize_whole[1] / 2) * counter
                - i * font_name,
                line,
            )
        barcode = selectBarcodeType(
            c,
            type_code,
            code,
            filepath=filepath,
            pagesize=(pagesize_whole[0], pagesize_whole[1] / 2),
            y_offset=pagesize_whole[1] / 2 - (pagesize_whole[1] / 2) * counter - 4 * mm,
            x=5 * mm,
            y=0,
            bar_height=height_barcode,
            bar_width=width_barcode,
        )
        text_sku = VerticalText(f"SKU: {sku}")
        text_sku.drawOn(
            c,
            2 * mm,
            pagesize_whole[1]
            - pagesize_whole[1] / 2
            + 1 * mm
            - (pagesize_whole[1] / 2) * counter,
        )
        text_code = VerticalText(text=str(code))
        text_code.drawOn(
            c,
            pagesize_whole[0] - 5 * mm,
            pagesize_whole[1]
            - pagesize_whole[1] / 2
            + 1 * mm
            - (pagesize_whole[1] / 2) * counter,
        )

        counter += 1
        if counter == code_per_page:
            c.showPage()
            counter = 0
    c.save()


def create_multiple_element_from_pdf(pagesize, filepath, **kwargs):
    pdf_document = fitz.open(filepath)
    pagesize = get_page_size(pagesize)
    pagesize_image = get_page_size(kwargs.get("pagesize_image", "default"))
    orientation_image = kwargs.get("orientation_image", "horizontal")
    orientation = kwargs.get("orientation", "vertical")
    pagesize = (pagesize[1], pagesize[0]) if orientation == "horizontal" else pagesize
    pagesize_image = (
        (pagesize_image[1], pagesize_image[0])
        if orientation_image == "horizontal"
        else pagesize_image
    )
    x_init = kwargs.get("x_init", 0)
    y_init = kwargs.get("y_init", 0)
    columns = kwargs.get("columns", 2)
    rows = kwargs.get("rows", 12)
    pages = pdf_document.page_count
    c = canvas.Canvas(filepath.replace(".pdf", "_multiple.pdf"), pagesize=pagesize)
    new_pages = pages // (columns * rows) + 1
    page_number = 0
    for page in range(new_pages):
        for i in range(rows):
            for j in range(columns):
                if page_number == pages:
                    break
                page = pdf_document.load_page(page_number)
                pix = page.get_pixmap()
                image_io = BytesIO()
                pil_image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                pil_image.save(image_io, format="PNG")
                image_io.seek(0)
                # temp_file_img = "files/temp_img.png"
                # image.save(temp_file_img)
                image_reader = ImageReader(image_io)
                x = pagesize[0] / columns * j + x_init
                y = (
                    pagesize[1]
                    - pagesize_image[1] * 2
                    - (pagesize[1] / rows * i + y_init)
                )
                c.drawImage(
                    image_reader,
                    x,
                    y,
                    width=pagesize[0] / columns,
                    height=pagesize[1] / rows,
                )
                page_number += 1
            if page_number == pages:
                break
        c.showPage()
    c.save()
    pdf_document.close()
    print("Multiple elements created: ", filepath.replace(".pdf", "_multiple.pdf"))
