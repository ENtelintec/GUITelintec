# -*- coding: utf-8 -*-
from templates.controllers.material_request.sm_controller import insert_sm_db
__author__ = "Edisson Naula"
__date__ = "$ 10/sept/2025  at 9:15 $"

import json
import os
import re

import pandas as pd

from static.constants import format_timestamps
from templates.controllers.employees.employees_controller import get_employee_id_name

if __name__ == "__main__":
    path_folder = "files/db_files/"
    files = os.listdir(path_folder)
    # Patrón regex para extraer "SM-0701-xxx"
    patron = r"SM-SGI-(\d{3})"
    # Extraer coincidencias
    folios = [
        re.search(patron, archivo).group()
        for archivo in files
        if re.search(patron, archivo)
    ]
    name_to_id = {}
    # open files with pandas
    for file in files:
        # saltar filas hasta la 11
        # usar hasta la columna 8
        if "~$" in file:
            continue
        df = pd.read_excel(
            path_folder + file,
            skiprows=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            engine="openpyxl",
            usecols=[0, 1, 2, 3, 4, 5, 6, 7],
        )
        df_metadata = pd.read_excel(
            path_folder + file, skiprows=3, nrows=7, header=None, engine="openpyxl"
        )  # Lee solo las primeras 10 filas
        df_metadata = df_metadata.dropna(axis=1, how="all")
        # Mostrar resultados organizados
        array_metadata = df_metadata.values.tolist()
        # make nan or nat blank spaces
        array_metadata = [
            ["" if pd.isna(x) else x for x in row] for row in array_metadata
        ]
        date_sm = (
            pd.to_datetime(array_metadata[0][1], dayfirst=True, errors="coerce")
            if isinstance(array_metadata[0][1], str)
            else array_metadata[0][1]
        )
        critical_date = (
            pd.to_datetime(array_metadata[5][3], dayfirst=True, errors="coerce")
            if isinstance(array_metadata[5][3], str)
            else array_metadata[5][3]
        )

        metadata = {
            "date": date_sm.strftime(format_timestamps),
            "folio": array_metadata[0][3].upper(),
            "contract": "RFID",
            "contract_contact": array_metadata[2][3]
            if isinstance(array_metadata[2][3], str)
            else None,
            "order_quotation": array_metadata[3][1],
            "emp_name": array_metadata[3][3],
            "facility": array_metadata[4][1],
            "destination": array_metadata[4][3],
            "location": array_metadata[5][1],
            "critical_date": critical_date.strftime(format_timestamps)
            if isinstance(critical_date, str)
            else None,
            "client_id": 40,
            "status": 0,
            "comment": "",
        }
        if metadata["emp_name"].lower() in name_to_id:
            metadata["emp_id"] = name_to_id[metadata["emp_name"].lower()]
        else:
            result, error = get_employee_id_name(metadata["emp_name"].lower())
            if result is not None:
                metadata["emp_id"] = result
                name_to_id[metadata["emp_name"].lower()] = result
            else:
                metadata["emp_id"] = 10
        # Encontrar la primera fila completamente vacía
        indice_fila_vacia = df[df.isnull().all(axis=1)].index.min()
        # Filtrar los datos hasta esa fila
        if pd.notna(indice_fila_vacia):  # Verificar que se encontró una fila vacía
            df = df.loc[: indice_fila_vacia - 1]  # Mantener solo hasta la fila vacía

        df = df.dropna(axis=1, how="all")
        items = []
        for _, row in df.iterrows():
            items.append(
                {
                    "id": 0,
                    "partida": row.iloc[0],
                    "name": row.iloc[1],
                    "quantity": row.iloc[2],
                    "udm": row.iloc[3],
                    "movement": 0,
                    "comment": "",
                }
            )
        # print({"info": metadata, "items": items})
        # print("str", json.dumps({"info": metadata, "items": items}))
        flag, error, result = insert_sm_db({"info": metadata, "items": items})
        print(flag, error, result)
