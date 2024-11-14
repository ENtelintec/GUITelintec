# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 24/oct/2024  at 9:55 $"

from reportlab.graphics.barcode import code39, code128, code93
from reportlab.graphics.barcode import eanbc, qr, usps
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF

from templates.forms.PDFGenerator import wrap_text

default_size_page = (40.00 * mm, 76.00 * mm)
sizes_page = {
    "A4": (210 * mm, 297 * mm),
    "A5": (148 * mm, 210 * mm),
    "A6": (105 * mm, 148 * mm),
    "A7": (74 * mm, 105 * mm),
    "A8": (52 * mm, 74 * mm),
    "A9": (37 * mm, 52 * mm),
    "A10": (26 * mm, 37 * mm),
    "default": default_size_page,
}

data_company = {"name": "Telintec", "department": "Almacen"}


def BarCode39(filepath, code, x, y, size=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)
    barcode39 = code39.Extended39(code)
    barcode39.drawOn(c, 1 * mm, 1 * mm)
    return barcode39


def BarCode39Std(filepath, code, x, y, size=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)

    barcode39 = code39.Standard39(code)

    barcode39.drawOn(c, 1 * mm, 1 * mm)
    return barcode39


def BarCode128(c, code, y_offset, pagesize=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    bar_height = 10 * mm
    bar_width = 0.5 * mm
    barcode128 = code128.Code128(
        code,
        barHeight=bar_height,
        barWidth=bar_width,
    )
    width, height = (barcode128.width, barcode128.height)
    x = (pagesize[0] - width) / 2
    y = ((pagesize[1] - height) / 2) - y_offset
    barcode128.drawOn(c, x, y)
    return barcode128


def BarCode93(filepath, code, x, y, size=default_size_page):
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


def BarCodeUSPS(filepath, code, x, y, size=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)

    barcode_usps = usps.POSTNET(code)

    barcode_usps.drawOn(c, 1 * mm, 1 * mm)
    return barcode_usps


def BarCodeEANBC8(filepath, code, x, y, size=default_size_page):
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


def BarCodeEANBC13(filepath, code, x, y, size=default_size_page):
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


def BarCodeQR(filepath, code, x, y, size=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)

    qr_code = qr.QrCodeWidget(code)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(45, 45, transform=[45.0 / width, 0, 0, 45.0 / height, 0, 0])
    d.add(qr_code)
    renderPDF.draw(d, c, 1, 1)
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


def create_BarCodeFormat(
    code, sku, name, filepath, type_code, pagesize="default", orientation="horizontal"
):
    pagesize = sizes_page[pagesize]
    pagesize = (pagesize[1], pagesize[0]) if orientation == "horizontal" else pagesize
    c = canvas.Canvas(filepath, pagesize=pagesize)
    draw_border(c, 0, 0, pagesize[0], pagesize[1])
    c.setFont("Helvetica", 14)
    c.drawCentredString(
        pagesize[0] / 2,
        pagesize[1] - 18,
        f"{data_company['name']}-{data_company['department']}",
    )
    name_list = wrap_text(name.upper(), pagesize[0] - 5 * mm).split("\n")
    font_name = 9
    c.setFont("Courier-Bold", font_name)
    for i, line in enumerate(name_list):
        c.drawString(5 * mm, pagesize[1] - 30 - i * font_name, line)
    c.setFont("Helvetica", 6)
    c.drawString(5 * mm, pagesize[1] - len(name_list) * font_name - 30, f"SKU: {sku}")
    match type_code:
        case "39":
            barcode = BarCode39(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "39std":
            barcode = BarCode39Std(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "93":
            barcode = BarCode93(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "128":
            barcode = BarCode128(c, code, 7 * mm, pagesize)
        case "usps":
            barcode = BarCodeUSPS(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "eanbc8":
            barcode = BarCodeEANBC8(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "eanbc13":
            barcode = BarCodeEANBC13(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "qr":
            barcode = BarCodeQR(filepath, code, 5 * mm, 5 * mm, pagesize)
        case _:
            barcode = None
            print("Error at creating barcode")
    height_barcode = barcode.height if barcode else 10
    c.setFont("Helvetica", 7)
    c.drawCentredString(
        pagesize[0] / 2, pagesize[1] / 2 - 20 - height_barcode / 2 - 8, code
    )
    c.save()
    print("Barcode created: ", filepath)
