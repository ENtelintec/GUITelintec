# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 26/nov/2024  at 14:35 $"

from reportlab.lib.units import mm

from static.constants import file_codebar


coldata_inventory = [
    {"text": "ID Producto", "stretch": True},
    {"text": "SKU", "stretch": True},
    {"text": "Nombre", "stretch": True},
    {"text": "UDM", "stretch": True},
    {"text": "Stock", "stretch": True},
    {"text": "Categoría", "stretch": True},
    {"text": "Proveedor", "stretch": True},
    {"text": "Herramienta", "stretch": True},
    {"text": "Interno", "stretch": True},
    {"text": "Codigos", "stretch": True},
    {"text": "Ubicaciones", "stretch": True},
]


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