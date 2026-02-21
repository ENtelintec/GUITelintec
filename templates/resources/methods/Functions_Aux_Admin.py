# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:40 $"

import json
import re

import pandas as pd
from PyPDF2 import PdfReader

from templates.controllers.product.p_and_s_controller import (
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


def read_exel_products_partidas(path: str):
    df = pd.read_excel(path)
    df = df.fillna("")
    data_excel = df.to_dict("records")

    products = []
    for index, item in enumerate(data_excel):
        # partida: number; quantity: number; udm: string; price_unit: number; type_p: string; marca: string; n_parte: string; description: string; description_small: string; id: number; comment: string;
        n_parte = item.get("NRO. PARTE", "")
        id_p = None
        if n_parte != "":
            flag, error, result = get_product_by_sku_manufacture(n_parte)
            if flag and len(result) > 0:
                id_p = result[0]
        product = {
            "partida": item.get("PARTIDA", index),
            "quantity": 1,
            "udm": item.get("UDM"),
            "price_unit": item.get("PRECIO UNITARIO", 0.0),
            "type_p": item.get("TIPO", ""),
            "marca": item.get("MARCA", ""),
            "n_parte": item.get("NRO. PARTE", ""),
            "description": item.get("DESCRIPCIÓN LARGA", ""),
            "description_small": item.get("DESCRIPCIÓN CORTA", ""),
            "id": id_p,
            "comment": "",
        }
        products.append(product)
    return products


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
