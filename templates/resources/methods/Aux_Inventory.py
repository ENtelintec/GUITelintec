# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 26/nov/2024  at 14:35 $"

from reportlab.lib.units import mm

from static.constants import file_codebar
from templates.controllers.product.p_and_s_controller import (
    get_all_products_db_old,
    get_all_movements_db_detail,
)

coldata_inventory = [
    {"text": "ID Producto", "stretch": False, "width": 80},
    {"text": "SKU", "stretch": False, "width": 80},
    {"text": "Nombre", "stretch": True},
    {"text": "UDM", "stretch": False, "width": 80},
    {"text": "Stock", "stretch": False, "width": 80},
    {"text": "Categoría", "stretch": False, "width": 80},
    {"text": "Proveedor", "stretch": False, "width": 80},
    {"text": "Herramienta", "stretch": False, "width": 80},
    {"text": "Interno", "stretch": False, "width": 80},
    {"text": "Codigos", "stretch": False, "width": 80},
    {"text": "Ubicaciones", "stretch": False, "width": 80},
    {"text": "Marca", "stretch": False, "width": 80},
    {"text": "Brands", "stretch": False, "width": 80},
]
coldata_movements = [
    {"text": "ID Movimiento", "stretch": False, "width": 40},
    {"text": "ID Producto", "stretch": False, "width": 40},
    {"text": "SKU", "stretch": False, "width": 90},
    {"text": "Tipo", "stretch": False, "width": 80},
    {"text": "Cantidad", "stretch": False, "width": 40},
    {"text": "Fecha", "stretch": False, "width": 110},
    {"text": "ID SM", "stretch": False, "width": 70},
    {"text": "Nombre", "stretch": True},
    {"text": "UDM", "stretch": False, "width": 40},
    {"text": "Fabricante", "stretch": False, "width": 120},
    {"text": "locations", "stretch": False, "width": 120},
    {"text": "Referencia", "stretch": False, "width": 90},
]
columns_inventory = [
    "ID",
    "SKU",
    "Producto",
    "UDM",
    "Cantidad",
    "Categoria",
    "Proveedor",
    "Herramienta?",
    "Interno?",
    "Codigos",
    "Ubicacion 1",
    "Marca",
]
columns_movements_widgets_lector = [
    "ID Producto",
    "Nombre",
    "Tipo",
    "Cantidad",
    "Fecha",
    "SM",
    "Old Stock",
    "Referencia",
]


def generate_default_configuration_barcodes(**kwargs):
    temp = kwargs.get("title_offset", "0, 0")
    title_offset_t = temp.split(",") if isinstance(temp, str) else temp
    title_offset = (
        (float(title_offset_t[0]), float(title_offset_t[1]))
        if len(title_offset_t) == 2
        else (0, 0)
    )
    temp = kwargs.get("code_offset", "0, 0")
    code_offset_t = temp.split(",") if isinstance(temp, str) else temp
    code_offset = (
        (float(code_offset_t[0]), float(code_offset_t[1]))
        if len(code_offset_t) == 2
        else (0, 0)
    )
    temp = kwargs.get("sku_offset", "0, 0")
    sku_offset_t = temp.split(", ") if isinstance(temp, str) else temp
    sku_offset = (
        (float(sku_offset_t[0]), float(sku_offset_t[1]))
        if len(sku_offset_t) == 2
        else (0, 0)
    )
    temp = kwargs.get("name_offset", "0, 0")
    name_offset_t = temp.split(", ") if isinstance(temp, str) else temp
    name_offset = (
        (float(name_offset_t[0]), float(name_offset_t[1]))
        if len(name_offset_t) == 2
        else (0, 0)
    )
    temp = kwargs.get("codebar_size", "0.4, 20")
    codebar_size_t = temp.split(",") if isinstance(temp, str) else temp
    codebar_size = (
        (float(codebar_size_t[0]), float(codebar_size_t[1]))
        if len(codebar_size_t) == 2
        else (0.4, 20)
    )
    temp = kwargs.get("codebar_offset", "0, -7")
    codebar_offset_t = temp.split(", ") if isinstance(temp, str) else temp
    codebar_offset = (
        (float(codebar_offset_t[0]), float(codebar_offset_t[1]))
        if len(codebar_offset_t) == 2
        else (0, -7)
    )
    name_width = int(kwargs.get("name_limit", 20))
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
        "name_width": name_width,
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


def fetch_all_products():
    flag, error, result = get_all_products_db_old()
    if not flag:
        print("Error al obtener los productos:", str(error))
        return []
    return result


def divide_movements(movements_data):
    """

    :param movements_data: data from all movements type
    :return: <ins>, <outs>  two list, one for ins and other for outs
    """
    if movements_data is None:
        return None, None
    ins = []
    outs = []
    for movement in movements_data:
        if movement[3] == "entrada":
            ins.append(movement)
        else:
            outs.append(movement)
    return ins, outs


def fetch_all_movements():
    flag, error, movements = get_all_movements_db_detail()
    if not flag:
        print("Error al obtener los movimientos:", str(error))
        return []
    return movements


def create_excel_file(data, filepath):
    """
    Create an Excel file with the data provided.

    :param data: {'col1': [1, 2], 'col2': [3, 4]}
    :param filepath:
    :return:
    """
    import pandas as pd

    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)
    return filepath
