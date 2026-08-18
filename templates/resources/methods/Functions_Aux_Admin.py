# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:40 $"

import json
import re

import pandas as pd
from PyPDF2 import PdfReader

from templates.controllers.product.products_controller import (
    get_product_by_sku_manufacture,
)


def parse_data(data: dict, mode: int):
    """
    Parses the data.
    :param data: <dict>
    :param mode: <int>
    :return: <dict>
    """
    code = 200
    try:
        match mode:
            case 1:
                out = {
                    "id": data["id"] if "id" in data.keys() else None,
                    "metadata": data["metadata"] if "metadata" in data.keys() else None,
                    "products": data["products"] if "products" in data.keys() else None,
                    "creation": data["creation"] if "creation" in data.keys() else None,
                    "timestamps": data["timestamps"]
                    if "timestamps" in data.keys()
                    else None,
                }
            case 2:
                out = {
                    "id": data["id"] if "id" in data.keys() else None,
                    "metadata": data["metadata"] if "metadata" in data.keys() else None,
                    "products": data["products"] if "products" in data.keys() else None,
                    "creation": data["creation"] if "creation" in data.keys() else None,
                    "timestamps": data["timestamps"]
                    if "timestamps" in data.keys()
                    else None,
                    "quotation_id": data["quotation_id"]
                    if "quotation_id" in data.keys()
                    else None,
                }
            case _:
                print("Invalid mode")
                code = 204
                out = {"error": "Invalid mode"}
    except Exception as e:
        print(e)
        code = 400
        out = {"error": "Invalid sintaxis" + str(e)}
    return code, out


def extract_number_pdf_contrac(txt: str):
    pattern = r"\d+.\d+,\d+"
    matches = re.findall(pattern, txt)
    if len(matches) == 0:
        pattern = r"\d+,\d+"
        matches = re.findall(pattern, txt)
    matches = matches if matches else ["0.0"]
    return matches[0] if isinstance(matches, list) else "0.0"


def normalize_row_contract_pdf(row_data):
    # remove elements with "" in the last position
    row_data = [item for item in row_data if item != ""]
    if len(row_data) == 6:
        return [
            int(row_data[0]),
            row_data[1],
            float(
                extract_number_pdf_contrac(row_data[2])
                .replace(".", "")
                .replace(",", ".")
            ),
            row_data[3],
            float(
                extract_number_pdf_contrac(row_data[4])
                .replace(".", "")
                .replace(",", ".")
            ),
            float(
                extract_number_pdf_contrac(row_data[5])
                .replace(".", "")
                .replace(",", ".")
            ),
        ]
    elif len(row_data) == 5:
        new_row = []
        for index_i, item in enumerate(row_data):
            pattern = r"[a-zA-Z]+\s.\d+.\d+,\d+"
            if re.findall(pattern, item):
                new_row += item.split(" ")
            else:
                new_row.append(item)
        new_row[0] = int(new_row[0])
        new_row[4] = float(new_row[4].replace(".", "").replace(",", "."))
        return new_row
    else:
        len_row = len(row_data)
        if len_row > 6:
            return row_data[:6]
        else:
            add = 6 - len_row
            row_data.extend([""] * add)
            return row_data


def read_file_tenium_contract(path: str, pattern, phrase):
    reader = PdfReader(path)
    flag2 = False
    data = []
    for i in range(11, len(reader.pages)):
        page = reader.pages[i]
        # extracting text from page
        text = page.extract_text()
        match = re.search(pattern, text)
        flag1 = False
        counter1 = 0
        counter_line = 0
        if match:
            row = []
            for line in text.split("\n"):
                if phrase in line:
                    flag2 = True
                    continue
                if re.search(pattern, line):
                    counter1 += 1
                    if counter1 == 2:
                        flag1 = True
                    continue
                if line.strip() != "" and flag1 and flag2:
                    pattern2 = r"\s\s+"
                    line = re.sub(pattern2, "-", line)
                    line = line.replace("-", "", 1)
                    items = line.split("-")
                    if len(items) >= 2:
                        counter_line += 1
                        if counter_line == 1:
                            row = items[0:2]
                        elif counter_line == 2:
                            counter_line = 0
                            data.append(row + items)
                            row = []
    products = []
    for index, row in enumerate(data):
        data[index] = normalize_row_contract_pdf(row)
        products.append(
            {
                "partida": data[index][0],
                "description": data[index][1],
                "quantity": data[index][2],
                "udm": data[index][3],
                "price": data[index][4],
                "importe": data[index][5],
            }
        )
    return products


def read_exel_products_bidding(path: str):
    df = pd.read_excel(path, skiprows=[0])
    df = df.fillna("")
    data_excel = df.to_dict("records")
    products = []
    for item in data_excel:
        product = {
            "partida": item[" # "],
            "description_small": item["Description"],
            "description": item["Long Description"],
            "client": item["Client"],
            "quantity": item["Requested quantity"],
            "udm": item["Unit of measure"],
            "date_needed": item["Date needed"],
            "price_unit": item["Unit price"],
        }
        products.append(product)
    return products


def _is_int_like(value) -> bool:
    """True si value se puede convertir a int (POS./PARTIDA numerica)."""
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def _find_partidas_header_row(raw, max_scan: int = 40):
    """Ubica la fila de encabezados de la tabla de partidas.

    La posicion NO es fija entre plantillas (CCTV la trae en la fila 20, CERRAMIENTOS
    en la 18), asi que se busca la primera fila cuyas celdas contengan un token de
    posicion (POS/PARTIDA) + descripcion (DESCRIP*) + precio (PRECIO*). Devuelve el
    indice de la fila o None si no la encuentra.
    """
    limit = min(len(raw), max_scan)
    for i in range(limit):
        cells = [str(v).strip().upper() for v in raw.iloc[i].tolist()]
        has_pos = any(c in ("POS.", "POS", "PARTIDA") or c.startswith("PARTIDA") for c in cells)
        has_desc = any(c.startswith("DESCRIP") for c in cells)
        has_price = any(c.startswith("PRECIO") for c in cells)
        if has_pos and has_desc and has_price:
            return i
    return None


def read_exel_products_partidas(path: str, data_token):
    """
    Lee las partidas de un Excel (plantilla de partidas de contrato o de
    remision) y las agrupa por seccion.

    Una "seccion" es un bloque de items bajo un titulo (p.ej. "REFACCIONES DE
    SIST. CERRAMIENTOS"); el titulo puede venir en la columna DESCRIPCION o en la
    columna POS./PARTIDA (fila sin precio ni unidad). La POS. reinicia por seccion,
    asi que ``partida`` se conserva por seccion y cada item/seccion lleva un
    ``section_index`` 0-based que es la llave real que distingue partidas repetidas.

    Devuelve una tupla ``(groups, diagnostics)``:
      - ``groups``: lista de ``{"section_index", "section_title", "section_type",
        "group_title", "items": [...]}`` o ``None`` si el archivo no se pudo leer
        (Excel invalido / sin la fila de encabezado).
      - ``diagnostics``: dict con detalle para reportar errores al front y al log
        (error de lectura, columnas encontradas/mapeadas, conteo de filas totales
        / partidas / secciones / ignoradas).
    """
    diagnostics: dict = {
        "read_error": None,
        "columns_found": [],
        "columns_mapped": {},
        "rows_total": 0,
        "items_parsed": 0,
        "sections": 0,
        "rows_skipped": 0,
    }
    try:
        raw = pd.read_excel(path, header=None)
    except Exception as e:
        diagnostics["read_error"] = str(e)
        return None, diagnostics

    header_idx = _find_partidas_header_row(raw)
    if header_idx is None:
        diagnostics["read_error"] = (
            "No se encontró la fila de encabezados de partidas "
            "(se buscó POS./PARTIDA + DESCRIPCIÓN + PRECIO en las primeras filas)."
        )
        return None, diagnostics

    # Construir el DataFrame usando la fila detectada como encabezado.
    df = raw.iloc[header_idx + 1:].reset_index(drop=True)
    df.columns = raw.iloc[header_idx].tolist()
    df = df.fillna("")

    # Resolucion tolerante de columnas: soporta la plantilla de partidas de
    # contrato (PARTIDA/UDM/PRECIO UNITARIO/DESCRIPCION LARGA...) y la de
    # remision (POS./UM/PRECIO UNIT./DESCRIPCION). Se compara por nombre
    # normalizado (strip + upper) contra listas de alias.
    col_lookup = {str(c).strip().upper(): c for c in df.columns}  # pyrefly: ignore

    def resolve(*aliases):
        for alias in aliases:
            if alias in col_lookup:
                return col_lookup[alias]
        return None

    col_partida = resolve("PARTIDA", "POS.", "POS", "POSICION", "POSICIÓN")
    col_desc = resolve(
        "DESCRIPCIÓN LARGA", "DESCRIPCION LARGA", "DESCRIPCIÓN", "DESCRIPCION"
    )
    col_desc_small = resolve("DESCRIPCIÓN CORTA", "DESCRIPCION CORTA")
    col_precio = resolve("PRECIO UNITARIO", "PRECIO UNIT.", "PRECIO UNIT", "PRECIO")
    col_cantidad = resolve("CANTIDAD", "CANT.", "CANT")
    col_udm = resolve("UDM", "UM", "U.M.", "UNIDAD")
    # SKU / numero de parte real: solo la columna UDM de la plantilla de
    # partidas lo trae; en la de remision "UM" es unidad de medida (SRV), no un
    # SKU, asi que no se dispara el lookup a BD.
    col_sku = resolve("UDM", "NRO. PARTE", "NRO PARTE", "N. PARTE", "NO. PARTE")

    diagnostics["columns_found"] = [str(c) for c in df.columns]  # pyrefly: ignore
    diagnostics["columns_mapped"] = {
        "partida": col_partida,
        "description": col_desc,
        "description_small": col_desc_small,
        "price_unit": col_precio,
        "quantity": col_cantidad,
        "udm": col_udm,
        "sku": col_sku,
    }

    def cell(item, col, default=""):
        return item.get(col, default) if col is not None else default

    def make_group(idx, title, items):
        # section_type siempre "general": el parser no infiere planta/reajuste;
        # el front/humano reclasifica.
        return {
            "section_index": idx,
            "section_title": title,
            "section_type": "general",
            "group_title": title,  # alias de compatibilidad
            "items": items,
        }

    data_excel = df.to_dict("records")
    diagnostics["rows_total"] = len(data_excel)
    groups = []
    current_index = 0
    current_title = "General"
    current_items = []

    for index, item in enumerate(data_excel):
        udm = cell(item, col_udm, "")
        precio = cell(item, col_precio, "")
        description = cell(item, col_desc, "")
        partida = cell(item, col_partida, index)
        partida_txt = str(partida).strip()
        desc_txt = str(description).strip()
        # Detectar titulo de seccion: fila sin precio ni unidad, con partida NO
        # numerica y texto en DESCRIPCION o en POS. (el titulo puede estar en
        # cualquiera de las dos columnas segun la plantilla).
        if precio == "" and udm == "" and not _is_int_like(partida) and (desc_txt or partida_txt):
            diagnostics["sections"] += 1
            title = desc_txt or partida_txt
            if current_items:
                # Cerrar la seccion en curso y avanzar el indice.
                groups.append(make_group(current_index, current_title, current_items))
                current_index += 1
                current_items = []
            # Si la seccion en curso aun no tiene items, este titulo solo la nombra
            # (p.ej. el primer titulo del archivo renombra la seccion 0 "General").
            current_title = title
            continue

        try:
            partida = int(partida)
        except (ValueError, TypeError):
            # Filas de pie de pagina / vacias (SUBTOTAL, IVA, TOTAL, firmas...)
            diagnostics["rows_skipped"] += 1
            continue

        sku = str(cell(item, col_sku, "")).strip()
        id_p = None
        if sku != "":
            flag, error, result = get_product_by_sku_manufacture(sku, data_token)
            if flag and len(result) > 0:
                id_p = result[0]

        product = {
            "partida": partida,
            "section_index": current_index,
            # section_title/section_type se denormalizan en cada item para que el
            # front pueda re-enviarlos tal cual al crear el contrato (mismo shape
            # que expone get_quotation). section_type siempre "general".
            "section_title": current_title,
            "section_type": "general",
            "quantity": cell(item, col_cantidad, 1),
            "udm": udm,
            "price_unit": cell(item, col_precio, 0.0),
            "type_p": cell(item, resolve("TIPO"), ""),
            "marca": cell(item, resolve("MARCA"), ""),
            "n_parte": sku,
            "description": description,
            "description_small": cell(item, col_desc_small, ""),
            "id": id_p,
            "comment": "",
        }
        current_items.append(product)

    # Agregar última sección
    if current_items:
        groups.append(make_group(current_index, current_title, current_items))
    diagnostics["items_parsed"] = sum(len(g["items"]) for g in groups)
    return groups, diagnostics

# def read_exel_products_partidas(path: str):
#     # skiprow from 1 to 21 in 21 the headers
#     df = pd.read_excel(path, header=20)
#     print(path, df.head())
#     df = df.fillna("")
#     data_excel = df.to_dict("records")
#     products = []
#     for index, item in enumerate(data_excel):
#         n_parte = item.get("NRO. PARTE", "")
#         id_p = None
#         if n_parte != "":
#             flag, error, result = get_product_by_sku_manufacture(n_parte)
#             if flag and len(result) > 0:
#                 id_p = result[0]
#         partida = item.get("PARTIDA", index)
#         try:
#             partida = int(partida)
#             product = {
#                 "partida": partida,
#                 "quantity": item.get("CANTIDAD", 1),
#                 "udm": item.get("UDM"),
#                 "price_unit": item.get("PRECIO UNITARIO", 0.0),
#                 "type_p": item.get("TIPO", ""),
#                 "marca": item.get("MARCA", ""),
#                 "n_parte": item.get("NRO. PARTE", ""),
#                 "description": item.get("DESCRIPCIÓN LARGA", ""),
#                 "description_small": item.get("DESCRIPCIÓN CORTA", ""),
#                 "id": id_p,
#                 "comment": "",
#             }
#             products.append(product)
#         except Exception as e:
#             # print(e)
#             continue
#     return products


def read_exel_products_quotation(path: str):
    df = pd.read_excel(path, skiprows=[0])
    df = df.fillna("")
    data_excel = df.to_dict("records")
    products = []
    for item in data_excel:
        if item["PARTIDA"] == "":
            continue
        product = {
            "partida": item["PARTIDA"],
            "revision": True if item["REVISAR"] == "REVISAR" else False,
            "type_p": item["TIPO"],
            "marca": item["MARCA"],
            "n_parte": item["NRO. PARTE"],
            "description_small": item["DESCRIPCIÓN CORTA"],
            "description": item["DESCRIPCIÓN LARGA"],
            "quantity": item["CANTIDAD"],
            "udm": item["UND"],
            "price_unit": item["PRECIO"],
            "comment": "",
            "id": None,
        }
        products.append(product)
    return products


def compare_vectors_quotation_contract(vector1, vector2):
    out = [
        vector2[6],
        vector2[11],
        vector2[7],
        vector2[1],
        vector2[9],
        round(vector2[9] * vector2[7], 2),
        vector2[3],
        vector2[2],
        vector2[5],
        vector2[10],
        "<-->",
        vector1[0],
        vector1[1],
        vector1[2],
        vector1[3],
        vector1[4],
        vector1[5],
    ]
    coldata_c = [
        "Partida",
        "Descripción",
        "Cantidad",
        "Unidad",
        "Precio Unitario",
        "Total",
        "Tipo",
        "Marca",
        "Nro. Parte",
        "Descripción Larga",
        " ",
        "Partida",
        "Descripción",
        "Cantidad",
        "Unidad",
        "Precio Unitario",
        "Importe",
    ]
    flag = False
    if (
        round(vector2[9], 2) - 0.01 <= vector1[4] <= round(vector2[9], 2) + 0.01
    ):  # company
        flag = True
    return flag, out, coldata_c


def compare_file_quotation(data_quotation, products_contract):
    if products_contract is None or len(products_contract) == 0:
        return {"data": [], "flags": [], "msg": "No data detected"}, 200
    products_quotation = json.loads(data_quotation[2])
    table_rows = []
    flags = []
    columns = []
    if len(products_contract) >= len(products_quotation):
        df = pd.DataFrame.from_records(products_quotation)
        for index, item1 in enumerate(products_contract):
            partida_1 = int(item1["partida"])
            item2 = df.loc[df["partida"] == partida_1].values.tolist()
            item2 = (
                item2[0]
                if item2
                else [None, "", "", "", "", "", 0, 0, False, 0.0, "", ""]
            )
            flag, result, columns = compare_vectors_quotation_contract(
                list(item1.values()), item2
            )
            table_rows.append(result)
            flags.append(flag)
    else:
        df = pd.DataFrame.from_records(products_contract)
        for index, item1 in enumerate(products_quotation):
            partida_1 = int(item1["partida"])
            item2 = df.loc[df["partida"] == partida_1].values.tolist()
            item2 = (
                item2[0]
                if item2
                else [None, "", "", "", "", "", 0, 0, False, 0.0, "", ""]
            )
            flag, result, columns = compare_vectors_quotation_contract(
                list(item2), item1
            )
            table_rows.append(result)
            flags.append(flag)
    # replace item " " in columns
    columns = [item if item != " " else "Separator" for item in columns]
    data_out = {"data": table_rows, "columns": columns, "flags": flags, "msg": "Ok"}
    return data_out, 200
