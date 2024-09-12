# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 20/jun./2024  at 15:40 $"

import re

from PyPDF2 import PdfReader


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
