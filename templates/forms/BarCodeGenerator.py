# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 24/oct/2024  at 9:55 $"

from reportlab.graphics.barcode import code39, code128, code93
from reportlab.graphics.barcode import eanbc, qr, usps
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF

default_size_page = (76.00 * mm, 40.00 * mm)

data_company = {"name": "Telintec", "department": "Almacen"}


def BarCode39(filepath, code, x, y, size=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)
    barcode39 = code39.Extended39(code)
    barcode39.drawOn(c, 1 * mm, 1 * mm)
    c.save()


def BarCode39Std(filepath, code, x, y, size=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)

    barcode39 = code39.Standard39(code)

    barcode39.drawOn(c, 1 * mm, 1 * mm)
    c.save()


def BarCode128(c, code, y_offset, pagesize=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    barcode128 = code128.Code128(code)
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
    c.save()


def BarCodeUSPS(filepath, code, x, y, size=default_size_page):
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas(filepath, pagesize=size)

    barcode_usps = usps.POSTNET(code)

    barcode_usps.drawOn(c, 1 * mm, 1 * mm)
    c.save()


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
    c.save()


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
    c.save()


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
    c.save()


def create_BarCodeFormat(code, filepath, type_code, pagesize=default_size_page):
    c = canvas.Canvas(filepath, pagesize=pagesize)
    c.setFont("Helvetica", 14)
    c.drawCentredString(pagesize[0] / 2, pagesize[1] - 10, data_company["name"])
    c.setFont("Helvetica", 10)
    c.drawCentredString(pagesize[0] / 2, pagesize[1] - 20, data_company["department"])
    match type_code:
        case "39":
            BarCode39(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "39std":
            BarCode39Std(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "93":
            BarCode93(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "128":
            BarCode128(c, code, 5 * mm, pagesize)
        case "usps":
            BarCodeUSPS(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "eanbc8":
            BarCodeEANBC8(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "eanbc13":
            BarCodeEANBC13(filepath, code, 5 * mm, 5 * mm, pagesize)
        case "qr":
            BarCodeQR(filepath, code, 5 * mm, 5 * mm, pagesize)
        case _:
            print("Error at creating barcode")
    c.save()
    print("Barcode created: ", filepath)
