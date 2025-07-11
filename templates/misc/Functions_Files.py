# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/nov./2023  at 17:37 $"

import csv
import json
import os
import pickle
import re
import warnings
from calendar import monthrange
from datetime import datetime
from typing import Any

import dropbox
import pandas as pd
import pytz

from static.constants import (
    secrets,
    cache_oct_file_temp_path,
    cache_oct_fichaje_path,
    quizzes_RRHH,
    conversion_quizzes_path,
    format_date,
    timezone_software,
    format_timestamps,
)
from templates.Functions_Text import clean_accents, compare_employee_name
from templates.controllers.employees.employees_controller import get_employee_id_name
from templates.controllers.fichajes.fichajes_controller import (
    update_fichaje_DB,
    insert_new_fichaje_DB,
    get_all_fichajes,
)


def check_only_read_conflict(name: str) -> bool:
    """
    Check if the file is read-only
    :param name: name of the file
    :return: True if the file is read only, False otherwise
    """
    ignore_patterns = [".*conflictos de solo lectura.*", ".*cache.*", ".*desktop.ini"]
    pattern = "|".join(ignore_patterns)
    if re.match(pattern, name):
        return True
    return False


def get_files_foldes_dropbox(fname: str, online=False) -> tuple[list[str], list[str]]:
    """
    Gets the files and folders from dropbox
    :param online:
    :param fname: Name of the folder
    :return: files and folders
    """
    folders = []
    files = []
    if online:
        try:
            dbx = dropbox.Dropbox(secrets["APP_DROPBOX_TOKEN"])
            print("Exploring: ", fname)
            data = dbx.files_list_folder(path=fname)
            for entry in data.entries:
                if hasattr(entry, "shared_folder_id"):
                    folders.append(entry.name) if not check_only_read_conflict(
                        entry.name
                    ) else None
                else:
                    files.append(entry.name) if not check_only_read_conflict(
                        entry.name
                    ) else None
        except Exception as e:
            print(e)
            print("Error dropbox")
    else:
        try:
            files_and_folders = os.listdir(fname)
            for item in files_and_folders:
                if os.path.isdir(fname + "/" + item):
                    folders.append(item) if not check_only_read_conflict(item) else None
                else:
                    files.append(item) if not check_only_read_conflict(item) else None
        except Exception as e:
            print(e)
            print("Error local")
    return files, folders


def map_dropbox_folders(fname: str, father=None, online=False):
    """
    Maps the dropbox folders and subfolders
    :param online:
    :param father:
    :param fname: Name of the folder-mapped
    :return: mapped folder
    """
    if father is None:
        father = ""
    files, folders = get_files_foldes_dropbox(fname, online)
    root_dir = DirectoryDbp(fname, father, files)
    for folder in folders:
        folder_name = fname + "/" + folder
        root_dir.add_child(map_dropbox_folders(folder_name, fname, online))
    return root_dir


def save_directory_index(rpaths: dict, exclude: list = None, online=False, father=""):
    """
    Saves the directory to a file
    :param father:
    :param online: Read in online dropbox or local files
    :param rpaths: directory to save
    :param exclude: a list of folders to exclude
    :return:
    """
    local_name = "_local" if not online else ""
    exclude = exclude if exclude is not None else []
    for item in rpaths:
        if item not in exclude:
            local_file = "files/folders_" + item + local_name + ".pkl"
            fdir = father + "/" + rpaths[item]
            directory = map_dropbox_folders(fdir, online=online)
            with open(local_file, "wb") as f:
                pickle.dump(directory, f)


def load_directory_file(paths: dict, exclude: list = None, local=False) -> list:
    """
    Loads the directory from a file
    :param local:
    :param exclude: List of folders to exclude
    :param paths: directory to load
    :return:
    """
    exclude = exclude if exclude is not None else []
    out = []
    for item in paths:
        if item not in exclude:
            local_name = "_local" if local else ""
            local_file = "files/folders_" + item + local_name + ".pkl"
            with open(local_file, "rb") as f:
                rdirectory = pickle.load(f)
            out.append(rdirectory)
    return out


def save_directory_dbp(paths, dir_list, local=False):
    """
    Saves the directory to a file
    :param local:
    :param paths: Directory to save
    :param dir_list: directory to save
    :return:
    """
    local_name = "_local" if local else ""
    for index, item in enumerate(paths):
        local_file = "files/folders_" + item + local_name + ".pkl"
        with open(local_file, "wb") as f:
            pickle.dump(dir_list[index], f)


def clean_date(dates: list) -> list:
    """
    Clean dates p. m. -> PM, a. m. -> AM, Fecha/hora -> None, # Contrato:: -> None
    :param dates: list of dates
    :return: cleaned dates
    """
    pattern1 = "p. m."
    pattern2 = "a. m."
    pattern3 = "Fecha/hora"
    pattern4 = "# Contrato::"
    for i, str_date in enumerate(dates):
        if str_date is not None:
            if pattern1 in str_date:
                dates[i] = str_date.replace(pattern1, "PM")
            if pattern2 in str_date:
                dates[i] = str_date.replace(pattern2, "AM")
            if pattern3 in str_date:
                dates[i] = None
            if pattern4 in str_date:
                dates[i] = None
    return dates


def clean_in_out(in_out: list) -> list:
    """
    Clean IN/OUT -> IN, OUT -> FUERA, None -> None
    :param in_out: list of IN/OUT
    :return: cleaned IN/OUT
    """
    for i, str_in_out in enumerate(in_out):
        if str_in_out is not None:
            if "OUT" in str_in_out:
                in_out[i] = "FUERA"
            if "IN" in str_in_out:
                in_out[i] = "IN"
        else:
            in_out[i] = ""
    return in_out


def clean_text(texts: list) -> tuple[list, list, list, list]:
    """
    Clean text -> None, Admitido -> Admitido, Rechazado -> Rechazado,
    Admitido (Card: #) -> Admitido, Rechazado (Card: #) -> Rechazado
    :param texts: list of texts
    :return: cleaned text
    """
    status = []
    auth = []
    name = []
    card = []
    in_out = []
    for i, text in enumerate(texts):
        if text is not None:
            pattern = r"'(.*?)'"
            match1 = re.findall(pattern, text)
            pattern = r"\((.*?)\)"
            match2 = re.findall(pattern, text)
            options = ["Admitido", "Admitted"]
            if options[0] in text or options[1] in text:
                status.append("Admitido")
                auth.append("NA")
                name.append(match1[0])
                card.append(match2[0].replace("Card: ", ""))
                in_out.append(match2[1])
            else:
                status.append("Rechazado")
                auth.append(match2[0])
                name.append(match1[0])
                card.append(match2[1].replace("Card: ", ""))
                in_out.append(match2[2])
        else:
            status.append("")
            auth.append("")
            name.append("")
            card.append("")
            in_out.append("")
    return status, name, card, in_out


def make_empty_zeros(txt: str) -> float:
    """
    Makes empty strings into 0.0
    :param txt:
    :return:
    """
    try:
        out = float(txt) if txt != "" and txt != " " else 0.0
    except Exception as e:
        print("Error at make_empy_zeros: ", e, txt)
        out = 0.0
    return out


def clean_data_contract(
    status, fechas, comments, extras, primas, in_door, out_door
) -> tuple[list, list, list, list, list, list, list]:
    """
    Cleans data from contract.csv

    :param status:
    :param fechas:
    :param comments:
    :param extras:
    :param primas:
    :param in_door:
    :param out_door:
    :return:
    """
    for i, item in enumerate(extras):
        extras[i] = make_empty_zeros(item)
    for i, item in enumerate(primas):
        primas[i] = "NO" if item == "" or None else "SI"
    for i, item in enumerate(fechas):
        fechas[i] = "" if "Unnamed" in item else item
    return status, fechas, comments, extras, primas, in_door, out_door


def clean_parenthesis_txt(name: str) -> str:
    """
    Removes parenthesis from the name
    :param name:
    :return:
    """
    match = re.findall("(\(.*\))", name)
    if len(match) > 0:
        name = name.replace(match[0], "")
    name = name.replace("  ", " ")
    return name


def get_data_from_cache_sheet(
    filepath: str, excel_file, sheet: str, inital_skip_rows
) -> list | None:
    """
    Gets data from cache
    :param filepath:
    :param excel_file:
    :param sheet:
    :param inital_skip_rows:
    :return: List with data in the file
    """
    if sheet == "VEHICULOS":
        return None
    skip_rows = [i for i in range(0, inital_skip_rows)]
    # skip_rows = [i for i in range(9)] + [i for i in range(13, 3142)]
    df = pd.read_excel(excel_file, skiprows=skip_rows, sheet_name=sheet)
    df.to_csv(filepath)
    data = []
    with open(
        filepath, mode="r", encoding="utf-8"
    ) as csv_file:  # "r" represents the read mode
        reader = csv.reader(csv_file)  # this is the reader object
        for item in reader:
            data.append(item)
    return data


def get_data_from_sliced(
    data_aux,
) -> tuple[list, list, list, list, list, list, list, str]:
    """
    Gets data from sliced file
    :param data_aux:
    :return:
    """
    status = []
    fechas = []
    comments = []
    extras = []
    primas = []
    in_door = []
    out_door = []
    name = ""
    for i in range(len(data_aux)):
        if i == 1:
            name = clean_accents(data_aux[i][1])
            name = clean_parenthesis_txt(name)
            for j in range(2, len(data_aux[i])):
                if j % 2 != 1:
                    in_door.append(data_aux[i][j])
                else:
                    out_door.append(data_aux[i][j])
        elif i == 0:
            for j in range(2, len(data_aux[i])):
                if j % 2 != 1:
                    fechas.append(data_aux[i][j])
                else:
                    status.append(data_aux[i][j])
        elif i == 2:
            for j in range(2, len(data_aux[i])):
                if j % 2 != 1:
                    comments.append(data_aux[i][j])
        elif i == 3:
            for j in range(2, len(data_aux[i])):
                if j % 2 != 1:
                    extras.append(data_aux[i][j])
                else:
                    primas.append(data_aux[i][j])
    return status, fechas, comments, extras, primas, in_door, out_door, name


def open_cache_file_contracts(filepath: str) -> dict:
    """
    Opens the cache file.
    If the file does not exist, returns an empty dictionary.
    :param filepath:
    :return:
    """
    try:
        with open(filepath, "rb") as f:
            contracts = pickle.load(f)
    except Exception as e:
        print("Error at opening the file cache: ", e, "initialiaze as {}")
        contracts = {}
    return contracts


def extract_data_file_contracts(filename: str) -> dict:
    """
    Extracts the data from a file from operations and from cache on a directory.
    :param filename:
    :return: {Contracts_name: {employee_name: {status: [], fechas: [],
    comments: [], extras: [], primas: [], in_door: [], out_door: []}}}
    """
    bad_names = []
    contracts = open_cache_file_contracts(cache_oct_fichaje_path)
    try:
        excel_file = pd.ExcelFile(filename)
        sheet_names = excel_file.sheet_names
        inital_skip_rows = 9
        bad_names = []
        for sheet in sheet_names:
            data = get_data_from_cache_sheet(
                cache_oct_file_temp_path, excel_file, sheet, inital_skip_rows
            )
            if data is None:
                continue
            contracts[sheet] = {} if sheet not in contracts.keys() else contracts[sheet]
            indexes = range(len(data))
            starting_indexes = [indexes[i] for i in range(0, len(indexes), 4)]
            data_sliced = [data[i : i + 4] for i in starting_indexes]
            try:
                for data_aux in data_sliced:
                    (
                        status,
                        fechas,
                        comments,
                        extras,
                        primas,
                        in_door,
                        out_door,
                        name,
                    ) = get_data_from_sliced(data_aux)
                    if name != "":
                        status, fechas, comments, extras, primas, in_door, out_door = (
                            clean_data_contract(
                                status,
                                fechas,
                                comments,
                                extras,
                                primas,
                                in_door,
                                out_door,
                            )
                        )
                        if name not in contracts[sheet].keys():
                            id2, name_db = get_employee_id_name(name)
                            contracts[sheet][name] = {}
                            contracts[sheet][name]["id"] = id2
                            contracts[sheet][name]["name_db"] = name_db
                        if contracts[sheet][name]["id"] is None:
                            bad_names.append(name)
                            continue
                        contracts[sheet][name]["fechas"] = fechas
                        contracts[sheet][name]["status"] = status
                        contracts[sheet][name]["comments"] = comments
                        contracts[sheet][name]["extras"] = extras
                        contracts[sheet][name]["primas"] = primas
                        contracts[sheet][name]["in_door"] = in_door
                        contracts[sheet][name]["out_door"] = out_door
            except Exception as e:
                print(e)
                print(f"Error: {e}")
                continue
    except Exception as e:
        print(f"Error: {e}")
    with open(cache_oct_fichaje_path, "wb") as file:
        pickle.dump(contracts, file)
    if len(bad_names) > 0:
        msg = "Se han encontrado los siguientes empleados no registrados:\n"
        for ename in bad_names:
            msg += ename + "\n"
        # messagebox.showinfo("Error", msg)
        print(f"Error: {msg}")
    return contracts


def get_name_id_contracts(
    contracts: dict, name: str
) -> tuple[Any, str] | tuple[None, str]:
    """
    Gets the name and id of an employee from a dictionary.
    :param contracts:
    :param name:
    :return:
    """
    for contract in contracts.keys():
        for emp in contracts[contract].keys():
            if (
                name.lower() == contracts[contract][emp]["name_db"].lower()
                or name.lower() == emp.lower()
            ):
                return contracts[contract][emp]["id"], contracts[contract][emp][
                    "name_db"
                ]
    return None, name


def clean_status_contracts(status: str):
    """
    Cleans the status of the contract
    :param status:
    :return:
    """
    return "" if "Unnamed" in status else status


def generate_table_from_dict_contracts(contracts: dict):
    """
    Generates a table from a dictionary with column headers and data.
    Columns are: Contrato, Empleado, ID, Fecha, Status, Extras, Primas, Entrada, Salida, Comentarios.
    :param contracts:
    :return:
    """
    table_data = []
    for con_name in contracts.keys():
        for emp_name in contracts[con_name].keys():
            if contracts[con_name][emp_name]["id"] is not None:
                for i in range(len(contracts[con_name][emp_name]["status"])):
                    table_data.append(
                        [
                            con_name,
                            emp_name,
                            contracts[con_name][emp_name]["id"],
                            contracts[con_name][emp_name]["fechas"][i],
                            clean_status_contracts(
                                contracts[con_name][emp_name]["status"][i]
                            ),
                            contracts[con_name][emp_name]["extras"][i],
                            contracts[con_name][emp_name]["primas"][i],
                            contracts[con_name][emp_name]["in_door"][i],
                            contracts[con_name][emp_name]["out_door"][i],
                            contracts[con_name][emp_name]["comments"][i],
                        ]
                    )
    columns = [
        "Contrato",
        "Empleado",
        "ID",
        "Fecha",
        "Status",
        "Extras",
        "Primas",
        "Entrada",
        "Salida",
        "Comentarios",
    ]
    return table_data, columns


def extract_fichajes_file(filename: str):
    """
    Extracts the data from a file
    :param filename:
    :return:
    """
    try:
        skip_rows = [0, 1, 2]
        cols = (
            [0, 1, 2]
            if "Ternium" in filename
            else [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        )
        warnings.simplefilter("ignore")
        # noinspection PyTypeChecker
        df = pd.read_excel(filename, skiprows=skip_rows)
        if "Ternium" in filename:
            df.dropna(inplace=True)
            df["Fecha/hora"] = clean_date(df["Fecha/hora"].tolist())
            df["Fecha/hora"] = pd.to_datetime(
                df["Fecha/hora"], format="mixed", dayfirst=True
            )
            df.dropna(subset=["Fecha/hora"], inplace=True)
            df["status"], df["name"], df["card"], df["in_out"] = clean_text(
                df["Texto"].to_list()
            )
            df["in_out"] = clean_in_out(df["in_out"].tolist())
        else:
            df.dropna(inplace=True)
            df = df[df["Fecha de fichaje a la entrada"] != "--"]
            df = df[df["Fecha de fichaje a la salida"] != "--"]
            df["Fecha/hora_in"] = (
                df["Fecha de fichaje a la entrada"]
                + " "
                + df["Hora de fichaje a la entrada"]
            )
            df.drop(
                columns=[
                    "Fecha de fichaje a la entrada",
                    "Hora de fichaje a la entrada",
                ],
                inplace=True,
            )
            df["Fecha/hora_out"] = (
                df["Fecha de fichaje a la salida"]
                + " "
                + df["Hora de fichaje a la salida"]
            )
            df.drop(
                columns=["Fecha de fichaje a la salida", "Hora de fichaje a la salida"],
                inplace=True,
            )
            df["Fecha/hora_in"] = pd.to_datetime(
                df["Fecha/hora_in"], format="mixed", dayfirst=True
            )
            df["Fecha/hora_out"] = pd.to_datetime(
                df["Fecha/hora_out"], format="mixed", dayfirst=True
            )
            df["Fecha"] = pd.to_datetime(df["Fecha"], format="mixed", dayfirst=True)
            df["name"] = df["Nombre"].str.upper() + " " + df["Apellido"].str.upper()
            df["Horas trabajadas"] = transform_hours_to_float(
                df["Horas trabajadas"].tolist()
            )
            df.drop(columns=["Nombre", "Apellido"], inplace=True)
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None


class DirectoryDbp:
    def __init__(self, name: str, father: str, files: list, children=None):
        if children is None:
            children = []
        self.name = name
        self.father = father
        self.children = children
        self.files = files

    def add_file(self, file: str):
        self.files.append(file)
        return len(self.files)

    def add_child(self, child):
        self.children.append(child)
        return len(self.children)

    def __str__(self):
        return (
            self.name
            + " "
            + str(self.father)
            + " "
            + str(len(self.children))
            + " "
            + str(len(self.files))
        )

    def __repr__(self):
        return self.name


def get_dict_fichaje(dict_list: list[dict], data: list[dict]):
    for i, item_dict in enumerate(data):
        dict_f = dict_list[i]
        if item_dict is not None:
            for timestamp_key, item in item_dict.items():
                timestamp = (
                    datetime.strptime(timestamp_key, format_timestamps)
                    if isinstance(timestamp_key, str)
                    else timestamp_key
                )
                year = str(timestamp.year)
                month = str(timestamp.month)
                day = str(timestamp.day)
                value, comment = item
                if year not in dict_f.keys():
                    dict_f[year] = {}
                    dict_f[year][month] = {}
                    dict_f[year][month][day] = {}
                    dict_f[year][month][day]["timestamp"] = str(timestamp)
                    dict_f[year][month][day]["comment"] = comment
                    dict_f[year][month][day]["value"] = value.seconds // 3600
                elif month not in dict_f[year].keys():
                    dict_f[year][month] = {}
                    dict_f[year][month][day] = {}
                    dict_f[year][month][day]["timestamp"] = str(timestamp)
                    dict_f[year][month][day]["comment"] = comment
                    dict_f[year][month][day]["value"] = value.seconds // 3600
                elif day not in dict_f[year][month].keys():
                    dict_f[year][month][day] = {}
                    dict_f[year][month][day]["timestamp"] = str(timestamp)
                    dict_f[year][month][day]["comment"] = comment
                    dict_f[year][month][day]["value"] = value.seconds // 3600
                else:
                    dict_f[year][month][day]["timestamp"] = str(timestamp)
                    dict_f[year][month][day]["comment"] = comment
                    dict_f[year][month][day]["value"] = value.seconds // 3600
        dict_list[i] = dict_f
    return tuple(dict_list)


def get_dict_oct(dict_o: list[dict], data: list[list]):
    for i, list_data in enumerate(data):
        aux_dic = dict_o[i]
        if list_data is not None:
            for row in list_data:
                if len(row) == 2:
                    timestamp, comment = row
                    value = None
                else:
                    timestamp, comment, value = row
                timestamp = datetime.strptime(timestamp, format_timestamps)
                year = str(timestamp.year)
                month = str(timestamp.month)
                day = str(timestamp.day)
                if year not in aux_dic.keys():
                    aux_dic[year] = {}
                    aux_dic[year][month] = {}
                    aux_dic[year][month][day] = {}
                    aux_dic[year][month][day]["timestamp"] = str(timestamp)
                    aux_dic[year][month][day]["comment"] = comment
                    aux_dic[year][month][day]["value"] = value
                elif month not in aux_dic[year].keys():
                    aux_dic[year][month] = {}
                    aux_dic[year][month][day] = {}
                    aux_dic[year][month][day]["timestamp"] = str(timestamp)
                    aux_dic[year][month][day]["comment"] = comment
                    aux_dic[year][month][day]["value"] = value
                elif day not in aux_dic[year][month].keys():
                    aux_dic[year][month][day] = {}
                    aux_dic[year][month][day]["timestamp"] = str(timestamp)
                    aux_dic[year][month][day]["comment"] = comment
                    aux_dic[year][month][day]["value"] = value
                else:
                    aux_dic[year][month][day]["timestamp"] = str(timestamp)
                    aux_dic[year][month][day]["comment"] = comment
                    aux_dic[year][month][day]["value"] = value
        dict_o[i] = aux_dic
    return tuple(dict_o)


def get_dic_from_list_fichajes(data_fichaje: tuple, **kwargs) -> tuple:
    """
    Gets a dictionary from a list of data from fichajes files.
    :param data_fichaje: <(missing_days, late_days, extra_days, days_w_primer)>
    :param kwargs:  additional data from other sources.
    Must have the same estructure as data_fichaje.
    Right now just acepted type of files is oct and ternium data.
    :return: Tuple(dic_list_missing, dic_list_late, dic_list_extra, dic_list_primes)
    """
    days_missing_o, days_late_o, days_extra_o, primes_o, normal_o, early_o, pasive_o = (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    days_missing_t, days_late_t, days_extra_t, primes_t, normal_t, early_t, pasive_t = (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    days_missing_f, days_late_f, days_extra_f, primes_f, normal_f, early_f, pasive_f = (
        data_fichaje
    )
    for key, value in kwargs.items():
        if key == "oct_file":
            days_missing_o, days_late_o, days_extra_o, primes_o, normal_o = value
        elif key == "ternium_file":
            days_missing_t, days_late_t, days_extra_t, primes_t, normal_t = value
    days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic = (
        {},
        {},
        {},
        {},
        {},
    )
    days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic = (
        get_dict_fichaje(
            [
                days_missing_dict,
                days_late_dict,
                days_extra_dict,
                primes_dict,
                normal_dic,
            ],
            [days_missing_f, days_late_f, days_extra_f, primes_f, normal_t],
        )
    )
    days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic = (
        get_dict_oct(
            [
                days_missing_dict,
                days_late_dict,
                days_extra_dict,
                primes_dict,
                normal_dic,
            ],
            [days_missing_o, days_late_o, days_extra_o, primes_o, normal_o],
        )
    )
    days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic = (
        get_dict_fichaje(
            [
                days_missing_dict,
                days_late_dict,
                days_extra_dict,
                primes_dict,
                normal_dic,
            ],
            [days_missing_t, days_late_t, days_extra_t, primes_t, normal_t],
        )
    )
    return days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic


def get_cumulative_data_fichajes_dict(dic_data: dict, date=None) -> tuple[int, int]:
    """
    Gets the cumulative data from a dictionary of data from fichajes files
    :param date: date since the data is taken into account
    :param dic_data:
    :return:
    """
    if date is not None:
        date = pd.to_datetime(date)
    total_days = 0
    total_value = 0
    if date is None:
        for year in dic_data.keys():
            for month in dic_data[year].keys():
                total_days += len(dic_data[year][month].keys())
                for day in dic_data[year][month].keys():
                    value = dic_data[year][month][day]["value"]
                    if value is not None and value != "":
                        total_value += value
    else:
        for year in dic_data.keys():
            for month in dic_data[year].keys():
                for day in dic_data[year][month].keys():
                    if (
                        date.month <= int(month)
                        and date.year <= int(year)
                        and date.day <= int(day)
                    ):
                        value = dic_data[year][month][day]["value"]
                        total_days += 1
                        if value is not None and value != "":
                            total_value += value
    return total_days, total_value


def retrieve_file_cache_data(filepath):
    try:
        with open(filepath, "rb") as file:
            data = pickle.load(file)
        return True, None, data
    except Exception as e:
        print(f"Error at reading file: {filepath}--{str(e)}")
        return False, e, []


def save_file_cache_data(filepath, data):
    try:
        with open(filepath, "wb") as file:
            pickle.dump(data, file)
        return True, None
    except Exception as e:
        print(f"Error at saving file: {filepath}--{str(e)}")
        return False, e


def update_cache_data(cache_data, new_data, id_emp_up=None, deletion=False):
    ids_old = [item[0] for item in cache_data]
    ids_new = [item[0] for item in new_data]
    data_insert = []
    if id_emp_up not in ids_old:
        for index_1, item_new in enumerate(new_data):
            (
                id_emp,
                name,
                contract,
                faltas,
                lates,
                total_lates,
                extras,
                total_extra,
                primas,
                faltas_dic,
                lates_dic,
                extras_dic,
                primas_dic,
                normal_dic,
                early_dic,
                pasiva_dic,
            ) = item_new
            if id_emp == id_emp_up:
                flag, error, result = insert_new_fichaje_DB(
                    id_emp,
                    contract,
                    faltas_dic,
                    lates_dic,
                    extras_dic,
                    primas_dic,
                    normal_dic,
                    early_dic,
                    pasiva_dic,
                )
                data_insert.append(result)
                if flag:
                    cache_data.append(item_new)
                    print("Fichaje added DB")
                else:
                    print("Error at creating new registry at DB")
                    print(error)
                break
    else:
        for index_1, item_new in enumerate(new_data):
            (
                id_emp,
                name,
                contract2,
                faltas2,
                lates2,
                total_lates2,
                extras2,
                total_extra2,
                primas2,
                faltas_dic2,
                lates_dic2,
                extras_dic2,
                primas_dic2,
                normal_dic2,
            ) = item_new
            if id_emp_up == id_emp:
                for index_0, item_0 in enumerate(cache_data):
                    if id_emp == item_0[0]:
                        (
                            id_emp_0,
                            name,
                            contract,
                            faltas,
                            lates,
                            total_lates,
                            extras,
                            total_extra,
                            primas,
                            faltas_dic,
                            lates_dic,
                            extras_dic,
                            primas_dic,
                            normal_dic,
                            early_dic,
                            pasiva_dic,
                        ) = cache_data[index_0]
                        if deletion:
                            faltas_dic = faltas_dic2
                            lates_dic = lates_dic2
                            extras_dic = extras_dic2
                            primas_dic = primas_dic2
                            normal_dic = normal_dic2
                        else:
                            faltas_dic.update(faltas_dic2)
                            lates_dic.update(lates_dic2)
                            extras_dic.update(extras_dic2)
                            primas_dic.update(primas_dic2)
                            normal_dic.update(normal_dic2)
                        new_faltas, new_faltas_value = (
                            get_cumulative_data_fichajes_dict(faltas_dic)
                        )
                        new_lates, new_lates_value = get_cumulative_data_fichajes_dict(
                            lates_dic
                        )
                        new_extras, new_extras_value = (
                            get_cumulative_data_fichajes_dict(extras_dic)
                        )
                        new_primas, new_primas_value = (
                            get_cumulative_data_fichajes_dict(primas_dic)
                        )
                        aux = (
                            id_emp,
                            name,
                            contract,
                            new_faltas,
                            new_lates,
                            new_lates_value,
                            new_extras,
                            new_extras_value,
                            new_primas,
                            faltas_dic,
                            lates_dic,
                            extras_dic,
                            primas_dic,
                            normal_dic,
                            early_dic,
                            pasiva_dic,
                        )
                        flag, error, result = update_fichaje_DB(
                            id_emp,
                            contract,
                            faltas_dic,
                            lates_dic,
                            extras_dic,
                            primas_dic,
                            normal_dic,
                            early_dic,
                            pasiva_dic,
                        )
                        if flag:
                            print(f"Fichaje updated DB: {id_emp}")
                            cache_data[index_0] = aux
                        else:
                            print("Error at updating DB")
                            print(error)
                        break
                break


def update_fichajes_resume_cache(filepath: str, data=None, just_file=False):
    """
    Updates the fichajes resume cache
    :param just_file:
    :param filepath:
    :param data:
    :return:
    """
    if not just_file:
        update, error, fichajes_resume = retrieve_file_cache_data(filepath)
    else:
        error = None
        fichajes_resume = data
    if len(fichajes_resume) == 0 or error is not None:
        fichajes_resume = data
        print("Replazing cache into db")
    elif not just_file:
        ids_old = {item[0] for item in fichajes_resume}
        ids_new = {item[0] for item in data}
        new_insert_ids = ids_new - ids_old
        for index_1, item_1 in enumerate(data):
            for index_0, item_0 in enumerate(fichajes_resume):
                if item_1[0] == item_0[0] and item_0[2] == item_1[2]:
                    (
                        id_emp,
                        name,
                        contract,
                        faltas,
                        lates,
                        total_lates,
                        extras,
                        total_extra,
                        primas,
                        *dicts_old,
                    ) = fichajes_resume[index_0]
                    (
                        id_emp2,
                        name2,
                        contract2,
                        faltas2,
                        lates2,
                        total_lates2,
                        extras2,
                        total_extra2,
                        primas2,
                        *dicts_new,
                    ) = data[index_1]
                    new_total = []
                    new_value = []
                    for i in range(len(dicts_old)):
                        dicts_old[i].update(dicts_new[i])
                        new_total.append(
                            get_cumulative_data_fichajes_dict(dicts_old[i])[0]
                        )
                        new_value.append(
                            get_cumulative_data_fichajes_dict(dicts_old[i])[1]
                        )
                    aux = (
                        id_emp,
                        name,
                        contract,
                        new_total[0],
                        new_total[1],
                        new_value[1],
                        new_total[3],
                        new_value[3],
                        new_total[4],
                        dicts_new[0],
                        dicts_new[1],
                        dicts_new[2],
                        dicts_new[3],
                        dicts_new[4],
                        dicts_new[5],
                        dicts_new[6],
                    )
                    flag, error, result = update_fichaje_DB(
                        id_emp,
                        contract,
                        dicts_new[0],
                        dicts_new[1],
                        dicts_new[2],
                        dicts_new[3],
                        dicts_new[4],
                        dicts_new[5],
                        dicts_new[6],
                    )
                    if flag:
                        print("Fichaje updated DB: ", id_emp)
                        fichajes_resume[index_0] = aux
                    else:
                        print("Error at updating DB")
                        print(error)
                    break
        for id_new in new_insert_ids:
            for item in data:
                (
                    id_emp2,
                    name2,
                    contract2,
                    faltas2,
                    lates2,
                    total_lates2,
                    extras2,
                    total_extra2,
                    primas2,
                    faltas_dic2,
                    lates_dic2,
                    extras_dic2,
                    primas_dic2,
                    normal_dic2,
                    early_dic2,
                    pasiva_dic2,
                ) = item
                if id_new == id_emp2:
                    aux = (
                        id_new,
                        name2,
                        contract2,
                        faltas2,
                        lates2,
                        total_lates2,
                        extras2,
                        total_extra2,
                        primas2,
                        faltas_dic2,
                        lates_dic2,
                        extras_dic2,
                        primas_dic2,
                        normal_dic2,
                        early_dic2,
                    )
                    flag, error, result = insert_new_fichaje_DB(
                        id_new,
                        contract2,
                        faltas_dic2,
                        lates_dic2,
                        extras_dic2,
                        primas_dic2,
                        normal_dic2,
                        early_dic2,
                        pasiva_dic2,
                    )
                    if flag:
                        fichajes_resume.append(aux)
                        print("Fichaje added DB")
                    else:
                        print("Error at creating new registry at DB")
                        print(error)
                    break
    flag, error = save_file_cache_data(filepath, fichajes_resume)
    print("Fichajes resume cache file rewrited function files")
    return flag, error


def get_fichajes_resume_cache(filepath, is_hard_update=False) -> tuple[list, bool]:
    """
    Gets the fichajes resume cache if exists else the data is obtained from the
    db, and then the cumulative values of absences, delays, extra hours and primes
    are calculated.
    :param is_hard_update:
    :param filepath:
    :return:
    """
    fichajes_resume = []
    flag = False
    if not is_hard_update:
        try:
            with open(filepath, "rb") as file:
                fichajes_resume = pickle.load(file)
            flag = (
                False if len(fichajes_resume) == 0 or fichajes_resume is None else True
            )
        except Exception as e:
            print("Error at getting cache file: ", e)
            fichajes_resume = []
            flag = False
    else:
        flag = False
    if not flag:
        "calling db, because file not founded or api request"
        flag, error, result = get_all_fichajes()
        if flag and len(result) > 0:
            fichajes_resume = []
            for row in result:
                name = row[0]
                lastname = row[1]
                id_fich = row[2]
                id_emp = row[3]
                contract = row[4]
                absences = row[5]
                lates = row[6]
                extras = row[7]
                primes = row[8]
                normal = row[9]
                early = row[10]
                pasiva = row[11]
                new_faltas, new_faltas_value = get_cumulative_data_fichajes_dict(
                    json.loads(absences)
                )
                new_tardanzas, new_tardanzas_value = get_cumulative_data_fichajes_dict(
                    json.loads(lates)
                )
                new_extras, new_extras_value = get_cumulative_data_fichajes_dict(
                    json.loads(extras)
                )
                new_primas, new_primas_value = get_cumulative_data_fichajes_dict(
                    json.loads(primes)
                )
                new_early, new_early_value = get_cumulative_data_fichajes_dict(
                    json.loads(early)
                )
                new_pasiva, new_pasiva_value = get_cumulative_data_fichajes_dict(
                    json.loads(pasiva)
                )
                new_row = (
                    id_emp,
                    name.title() + lastname.title(),
                    contract,
                    new_faltas,
                    new_faltas_value,
                    new_tardanzas,
                    new_extras,
                    new_extras_value,
                    new_primas,
                    json.loads(absences),
                    json.loads(lates),
                    json.loads(extras),
                    json.loads(primes),
                    json.loads(normal),
                    json.loads(early),
                    json.loads(pasiva),
                )
                fichajes_resume.append(new_row)
            update_fichajes_resume_cache(filepath, fichajes_resume, just_file=True)
        else:
            fichajes_resume = []
            print("Error at getting fichajes from sql: ", error)
            flag = False
    return fichajes_resume, flag


def get_fichajes_emp_cache(filepath) -> tuple[dict, bool]:
    """
    Gets the fichajes resume cache if exists else the data is obtained from the
    db, and then the cumulative values of absences, delays, extra hours and primes
    are calculated.
    :param filepath:
    :return:
    """
    try:
        with open(filepath, "rb") as file:
            data = pickle.load(file)
        flag = False if len(data) == 0 else True
    except Exception as e:
        print("Error at getting cache file: ", e)
        data = {}
        flag = False
    return data, flag


def update_fichajes_emp_cache(filepath: str, data: dict):
    """
    Updates the fichajescache file with the data provided. If the file does not exist,
    it is created. If the file exists, it is updated.
    :param filepath:
    :param data:
    :return:
    """
    with open(filepath, "wb") as file:
        pickle.dump(data, file)


def check_names_employees_in_cache(names: list, filepath: str) -> dict:
    """
    Checks if the names of the employees are in the cache file.
    :param names:
    :param filepath:
    :return:
    """
    fichajes_emp_dict, flag = get_fichajes_emp_cache(filepath)
    for name in names:
        if name not in fichajes_emp_dict.keys():
            id_emp, name_db = get_employee_id_name(name)
            if id_emp is not None:
                fichajes_emp_dict[name] = {
                    "id": id_emp,
                    "name_db": name_db.upper(),
                }
    update_fichajes_emp_cache(filepath, fichajes_emp_dict)
    return fichajes_emp_dict


def read_file_not(filepath) -> list[tuple]:
    """
    Read the file and return a list of tuples with the data of the file.
    :return: List of tuples with the data of the file.
    :rtype: List of tuples.
    """
    out = []
    with open(filepath, "r") as file:
        content = file.readlines()
        for item in content:
            out.append(tuple(item.split(",;")))
    return out


def get_ExMed_cache_file(filepath: str) -> tuple[bool, dict]:
    """
    Gets the ExMed cache file if exists.
    :param filepath:
    :return:
    """
    try:
        with open(filepath, "rb") as file:
            exmed_cache = pickle.load(file)
        flag = False if len(exmed_cache) == 0 else True
    except Exception as e:
        print("Error at getting cache file: ", e)
        exmed_cache = None
        flag = False
    return flag, exmed_cache


def update_ExMed_cache_file(filepath: str, data: list):
    """
    Updates the ExMed cache file.
    :param filepath:
    :param data:
    :return:
    """
    with open(filepath, "wb") as file:
        pickle.dump(data, file)
    return True, None


def open_file_settings(filepath: str) -> tuple[bool, dict]:
    """
    Opens the json settings file.
    :param filepath:
    :return:
    """
    settings_default = {
        "max_chats": "40",
        "start_date": "19\/oct.\/2023",
        "end_date": "19\/oct.\/2023",
        "sampling_time": 1,
        "gui": {
            "null": {"theme": "litera"},
            "RRHH": {
                "days_asueto": ["01-01", "14-09"],
                "theme": "morph",
                "files_procces": "C:\/Users\/Edisson\/OneDrive\/Documentos\/Telintec_files_departments\/RH",
                "files_cache": "C:\/Users\/Edisson\/OneDrive\/Documentos\/Telintec_files_departments\/RH",
                "files_quizz_out": "files\/quizz_out\/",
            },
            "default": {"theme": "morph"},
        },
    }
    if not os.path.exists(filepath):
        return False, settings_default
    # Open the file and read the data.
    try:
        with open(filepath, "r") as file:
            settings = json.load(file)
        return True, settings
    except Exception as e:
        print("Error at opening file: ", e)
        return False, settings_default


def update_file_settings(filepath: str, settings: dict):
    """
    Updates the json settings file.
    :param filepath:
    :param settings:
    :return:
    """
    # Open the file and read the data.
    if not os.path.exists(filepath):
        with open(filepath, "w") as file:
            json.dump(settings, file)
        return True, None
    # Open the file and read the data.
    with open(filepath, "r") as file:
        data = json.load(file)
    data.update(settings)
    # Open the file and write the data.
    with open(filepath, "w") as file:
        json.dump(data, file)
    return True, None


def unify_data_display_fichaje(data: list[tuple[any, float, str]]) -> dict:
    """
    Unifies the data to be displayed in the fichaje frame.
    :param data: List of tuples fills with <timestamp, value, comment>
    :return:
    """
    dic_out = {}
    for item in data:
        timestamp, value, comment = item
        if isinstance(value, pd.Timedelta):
            value = value.total_seconds() / 3600
        comment = "Sin registro\n" if comment is None else comment
        timestamp = (
            datetime.strptime(timestamp, format_timestamps)
            if isinstance(timestamp, str)
            else timestamp
        )
        year = timestamp.year
        month = timestamp.month
        day = timestamp.day
        new_timestamp = datetime(year, month, day).strftime(format_date)
        if new_timestamp not in dic_out.keys():
            dic_out[new_timestamp] = [value, comment, [timestamp]]
        else:
            dic_out[new_timestamp][0] += float(value)
            dic_out[new_timestamp][1] += comment
            dic_out[new_timestamp][2].append(timestamp.strftime(format_timestamps))
    return dic_out


def correct_repetitions(
    normal_data_emp: dict,
    absence_data_emp: dict,
    prime_data_emp: dict,
    late_data_emp: dict,
    extra_data_emp: dict,
    early_data_emp=None,
    pasive_data_emp=None,
):
    keys_absence = absence_data_emp.keys()
    for key in normal_data_emp.keys():
        if key in keys_absence:
            res = absence_data_emp.pop(key, None)
    return (
        normal_data_emp,
        absence_data_emp,
        prime_data_emp,
        late_data_emp,
        extra_data_emp,
        early_data_emp,
        pasive_data_emp,
    )


def unify_data_employee(
    data_normal: list,
    data_absence: list,
    data_prime: list,
    data_late: list,
    data_extra: list,
    data_early=None,
    data_pasive=None,
) -> tuple:
    # normal data
    normal_data = []
    for group in data_normal:
        if group is None:
            continue
        for item in group:
            timestamp = None
            value = 1.0
            comment = None
            if isinstance(item, list):
                timestamp = item[0]
                if len(item) > 2:
                    value = item[1]
                    comment = f"------Fichaje------\nEntrada: {item[2]}\n"
                    comment += f"Salida: {item[3]}"
                else:
                    comment = f"------Ternium------\nPuerta ternium: {item[1]}\n"
            elif isinstance(item, tuple):
                timestamp, comment, value = item
                comment = f"------Bitacora------\n{comment}\n"
            normal_data.append((timestamp, value, comment))
    normal_data_emp = unify_data_display_fichaje(normal_data)
    # absence data
    absence_data = []
    for group in data_absence:
        if group is None:
            continue
        for item in group:
            value = 1.0
            comment = None
            if isinstance(item, tuple):
                timestamp, comment, value = item
                comment = f"------Bitacora------\n{comment}\n"
            else:
                timestamp = item
            absence_data.append((timestamp, value, comment))
    absence_data_emp = unify_data_display_fichaje(absence_data)
    # prime data
    prime_data = []
    for group in data_prime:
        if group is None:
            continue
        for item in group:
            if isinstance(item, tuple):
                timestamp, comment, value = item
                comment = f"------Bitacora------\n{comment}\n"
                prime_data.append((timestamp, value, comment))
    prime_data_emp = unify_data_display_fichaje(prime_data)
    # late data
    late_data = []
    for group in data_late:
        if group is None:
            continue
        if isinstance(group, dict):
            for k, v in group.items():
                late_data.append(
                    (k, v[0], f"------Fichaje------\nPuerta entrada: {v[1]}")
                )
        else:
            for item in group:
                if isinstance(item, tuple):
                    timestamp, comment, value = item
                    comment = f"------Bitacora------\n{comment}"
                    late_data.append((timestamp, value, comment))
    late_data_emp = unify_data_display_fichaje(late_data)
    # extra data
    extra_data = []
    for group in data_extra:
        if group is None:
            continue
        if isinstance(group, dict):
            for k, v in group.items():
                extra_data.append(
                    (k, v[0], f"------Fichaje------\nPuerta salida: {v[1]}")
                )
        else:
            for item in group:
                if isinstance(item, tuple):
                    timestamp, comment, value = item
                    comment = f"------Bitacora------\n{comment}"
                    extra_data.append((timestamp, value, comment))
    extra_data_emp = unify_data_display_fichaje(extra_data)
    early_data = []
    for group in data_early:
        if group is None:
            continue
        for item in group:
            if isinstance(item, tuple):
                timestamp, comment, value = item
                comment = f"------Bitacora------\n{comment}"
                early_data.append((timestamp, value, comment))
    early_data = unify_data_display_fichaje(early_data)
    pasive_data = []
    for group in data_pasive:
        if group is None:
            continue
        for item in group:
            if isinstance(item, tuple):
                timestamp, comment, value = item
                comment = f"------Bitacora------\n{comment}"
                pasive_data.append((timestamp, value, comment))
    pasive_data = unify_data_display_fichaje(pasive_data)
    (
        normal_data_emp,
        absence_data_emp,
        prime_data_emp,
        late_data_emp,
        extra_data_emp,
        early_data_emp,
        data_pasive_emp,
    ) = correct_repetitions(
        normal_data_emp,
        absence_data_emp,
        prime_data_emp,
        late_data_emp,
        extra_data_emp,
        early_data,
        pasive_data,
    )
    return (
        normal_data_emp,
        absence_data_emp,
        prime_data_emp,
        late_data_emp,
        extra_data_emp,
        early_data_emp,
        data_pasive_emp,
    )


def transform_hours_to_float(hours: list[str]):
    hour_out = []
    for hour in hours:
        hour = hour.split(":")
        hour = float(hour[0]) + float(hour[1]) / 60
        hour = round(hour, 2)
        hour_out.append(hour)
    return hour_out


def transform_hours_to_str(hours: float):
    hours_str = f"{int(hours):02}"
    hours_str += ":"
    hours_str += f"{int(round((hours - int(hours)) * 60, 0)):02}"
    return hours_str


def get_days_work(date: datetime):
    """
    Get the days of the month that are not sundays.
    :param date: The date.
    :return: The list of days.
    """
    n_days_month = monthrange(date.year, date.month)
    last_day = n_days_month[1] if n_days_month[1] <= date.day else date.day
    days_of_the_month = [i for i in range(1, last_day + 1)]
    # exclude sundays from the list
    work_days = []
    for day in days_of_the_month:
        date_aux = datetime(date.year, date.month, day)
        if date_aux.weekday() != 6:
            work_days.append(day)
    return work_days


def get_date_from_days_list(date: datetime, days: list):
    month = date.month
    year = date.year
    dates_list = []
    for day in days:
        timestamp = datetime(year, month, day)
        dates_list.append(timestamp)
    return dates_list


def get_worked_days(df_name: pd.DataFrame, type_f=1, month=None, date_max=None):
    if type_f == 1:
        days_worked = df_name["Fecha"].tolist()
        last_date = date_max if date_max is not None else days_worked[-1]
        if last_date is None:
            return [], []
        days_for_work = get_days_work(last_date)
        for day_worked in days_worked:
            if day_worked.day in days_for_work:
                days_for_work.remove(day_worked.day)
        days_not_worked = get_date_from_days_list(last_date, days_for_work)
        days_worked = df_name[
            [
                "Fecha",
                "Horas trabajadas",
                "Dispositivo de fichaje de entrada",
                "Dispositivo de fichaje de salida",
            ]
        ].values.tolist()
        return days_worked, days_not_worked
    else:
        days_worked = df_name["Fecha/hora"].tolist()
        # sort list by date
        last_date = days_worked[-1] if len(days_worked) > 0 else None
        month = last_date.month if month is None else month
        days_for_work = []
        if last_date is None:
            return [], []
        days_for_work = get_days_work(last_date)
        for day_worked in days_worked:
            if day_worked.day in days_for_work:
                days_for_work.remove(day_worked.day)
        days_not_worked = get_date_from_days_list(last_date, days_for_work)
        date_lower_limit = datetime(last_date.year, month, 1)
        days_worked = df_name[df_name["Fecha/hora"] >= date_lower_limit][
            ["Fecha/hora", "Puerta"]
        ].values.tolist()
        # days_worked = df_name[["Fecha/hora", "Puerta"]].values.tolist()
        return days_worked, days_not_worked


def get_info_f_file_name(
    df: pd.DataFrame,
    name: str,
    clocks,
    window_time_in,
    window_time_out,
    flag,
    date_max=None,
):
    """
        Get the information of the filename.
        Consider the most recent time is greater than the oldest time.
        Example:  if the fichaje time is 10:00 and the limit time is 09:00, then the function will return that
        timestamp as a late event.
        If the fichaje time is 08:00 and the limit time is 09:00, then the function
        will return that timestamp as an extra event.
        If the fichaje time is 19:00 and the limit time is 18:00,
        then the function will return that timestamp as an extra event.
        If the fichaje time is 17:00 and the limit
        time is 18:00, then the function will return that timestamp as an early event.

    :param df:
    :param name:
    :param date_max:
    :param df:
    :param name:
    :param clocks:
    :param window_time_in:
    :param window_time_out:
    :param flag:
    :param date_max: Most recent date to consider (.max())
    :return:
    """
    if not flag:
        return [], [], 0, 0, {}, {}, {}
    df_name = df[(df["name"] == name) & (df["Fecha/hora_in"] <= date_max)]
    days_worked, days_not_worked = get_worked_days(df_name, date_max=date_max)
    min_in = clocks[0]["entrada"][0].get()
    hour_in = clocks[0]["entrada"][1].get()
    min_out = clocks[1]["salida"][0].get()
    hour_out = clocks[1]["salida"][1].get()
    # filter late days and extra hours
    # set entrance hour
    aux_hour = int(hour_in) + int(window_time_in.get() / 60)
    aux_min = int(min_in) + int(window_time_in.get() % 60)
    limit_hour = pd.Timestamp(
        year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0
    )
    # count the number of rows where the person is late
    late_name = df_name[
        (df_name["Fecha/hora_in"].dt.time > limit_hour.time())
        & (df_name["Fecha/hora_in"] <= date_max)
    ]
    count_late = len(late_name)
    # calculate the time difference between the entrance hour and the limit hour
    late_dic = {}
    for i in late_name[["Fecha/hora_in", "Dispositivo de fichaje de entrada"]].values:
        time_str = pd.Timestamp(
            year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=0
        )
        late_dic[i[0]] = (time_str - limit_hour, i[1])
    # filter extra hours at entrance
    extra_name_in = df_name[
        (df_name["Fecha/hora_in"].dt.time <= limit_hour.time())
        & (df_name["Fecha/hora_in"] <= date_max)
    ]
    count_extra = 0
    count_extra += len(extra_name_in)
    extra_dic = {}
    for i in extra_name_in[
        ["Fecha/hora_in", "Dispositivo de fichaje de entrada"]
    ].values:
        time_str = pd.Timestamp(
            year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=0
        )
        extra_dic[i[0]] = (limit_hour - time_str, f"Entrada-->{i[1]}")
    # set exit hour
    aux_hour = int(hour_out) + int(window_time_out.get() / 60)
    aux_min = int(min_out) + int(window_time_out.get() % 60)
    limit_hour = pd.Timestamp(
        year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0
    )
    # count the number of rows where the person is with extra time
    extra_name_out = df_name[
        (df_name["Fecha/hora_out"].dt.time > limit_hour.time())
        & (df_name["Fecha/hora_out"] <= date_max)
    ]
    count_extra += len(extra_name_out)
    # calculate the time difference between the entrance hour and the extra hour
    extra_dic = {} if extra_dic is None else extra_dic
    for i in extra_name_out[
        ["Fecha/hora_out", "Dispositivo de fichaje de salida"]
    ].values:
        time_str = pd.Timestamp(
            year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=0
        )
        extra_dic[i[0]] = (time_str - limit_hour, f"Salida-->{i[1]}")
    # early leavings
    early_name = df_name[
        (df_name["Fecha/hora_out"].dt.time < limit_hour.time())
        & (df_name["Fecha/hora_out"] <= date_max)
    ]
    early_dic = {}
    for i in early_name[["Fecha/hora_out", "Dispositivo de fichaje de salida"]].values:
        time_str = pd.Timestamp(
            year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=0
        )
        early_dic[i[0]] = (limit_hour - time_str, f"Salida {i[1]}")
    return (
        days_worked,
        days_not_worked,
        count_late,
        count_extra,
        late_dic,
        extra_dic,
        early_dic,
    )


def get_info_t_file_name(
    df: pd.DataFrame,
    name: str,
    clocks,
    window_time_in,
    window_time_out,
    flag,
    month=None,
    date_max=None,
):
    if not flag:
        return "NA", "NA", "NA", "NA", {}, {}, [], [], {}
    date_min = pd.Timestamp(
        year=date_max.year, month=date_max.month, day=1, hour=0, minute=0, second=0
    )
    df_name = df[
        (df["name"] == name)
        & (df["Fecha/hora"] <= date_max)
        & (df["Fecha/hora"] >= date_min)
    ]
    days_worked, days_not_worked = get_worked_days(df_name, 2, month, date_max=date_max)
    df_name_entrada = df_name[
        (df_name["in_out"] == "DENTRO")
        & (df["Fecha/hora"] <= date_max)
        & (df["Fecha/hora"] >= date_min)
    ]
    df_name_salida = df_name[
        (df_name["in_out"] == "FUERA")
        & (df["Fecha/hora"] <= date_max)
        & (df["Fecha/hora"] >= date_min)
    ]
    worked_days = len(df_name["name"].to_list())
    min_in = clocks[0]["entrada"][0].get()
    hour_in = clocks[0]["entrada"][1].get()
    min_out = clocks[1]["salida"][0].get()
    hour_out = clocks[1]["salida"][1].get()
    # filter worked days
    df_name.set_index("Fecha/hora", inplace=True)
    worked_intime = len(
        df_name.between_time(
            start_time=f"{hour_in}:{min_in}:00", end_time=f"{hour_out}:{min_out}:00"
        )
    )
    # filter late days and extra hours
    # set entrance hour
    aux_hour = int(hour_in) + int(window_time_in.get() / 60)
    aux_min = int(min_in) + int(window_time_in.get() % 60)
    limit_hour = pd.Timestamp(
        year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0
    )
    # count the number of rows where the person is late
    late_name = df_name_entrada[
        (df_name_entrada["Fecha/hora"].dt.time > limit_hour.time())
        & (df_name_entrada["Fecha/hora"] <= date_max)
    ]
    count = len(late_name)
    # calculate the time difference between the entrance hour and the late hour
    time_late = {}
    for i in late_name[["Fecha/hora", "Puerta"]].values:
        time_str = pd.Timestamp(
            year=1,
            month=1,
            day=1,
            hour=i[0].hour,
            minute=i[0].minute,
            second=i[0].second,
        )
        diff = time_str - limit_hour
        time_late[i[0]] = (diff, i[1])
    # calculate the number of days when the person worked extra hours
    extra_time = {}
    extra_name_in = df_name_salida[
        (df_name_salida["Fecha/hora"].dt.time < limit_hour.time())
        & (df_name_salida["Fecha/hora"] <= date_max)
    ]
    count2 = len(extra_name_in)
    for i in extra_name_in[["Fecha/hora", "Puerta"]].values:
        time_str = pd.Timestamp(
            year=1,
            month=1,
            day=1,
            hour=i[0].hour,
            minute=i[0].minute,
            second=i[0].second,
        )
        diff = time_str - limit_hour
        extra_time[i[0]] = (diff, i[1])
    # set hour for leaving
    aux_hour = int(hour_out) + int(window_time_out.get() / 60)
    aux_min = int(min_out) + int(window_time_out.get() % 60)
    limit_hour2 = pd.Timestamp(
        year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0
    )
    extra_name = df_name_salida[
        (df_name_salida["Fecha/hora"].dt.time > limit_hour2.time())
        & (df_name_salida["Fecha/hora"] <= date_max)
    ]
    count2 += len(extra_name)
    extra_time = {} if extra_time is None else extra_time
    for i in extra_name[["Fecha/hora", "Puerta"]].values:
        time_str = pd.Timestamp(
            year=1,
            month=1,
            day=1,
            hour=i[0].hour,
            minute=i[0].minute,
            second=i[0].second,
        )
        diff = time_str - limit_hour2
        extra_time[i[0]] = (diff, i[1])
    ealy_name = df_name_salida[
        (df_name_salida["Fecha/hora"].dt.time < limit_hour2.time())
        & (df_name_salida["Fecha/hora"] <= date_max)
    ]
    early_time = {}
    for i in ealy_name[["Fecha/hora", "Puerta"]].values:
        time_str = pd.Timestamp(
            year=1,
            month=1,
            day=1,
            hour=i[0].hour,
            minute=i[0].minute,
            second=i[0].second,
        )
        diff = time_str - limit_hour2
        early_time[i[0]] = (diff, i[1])
    return (
        worked_days,
        worked_intime,
        count,
        count2,
        time_late,
        extra_time,
        days_worked,
        days_not_worked,
        early_time,
    )


def get_info_bitacora(df: pd.DataFrame, name: str, id_emp: int, flag, date_limit=None):
    if not flag:
        return 0.0, 0.0, 0.0, 0.0, [], [], [], [], [], [], []
    df_name = df[df["ID"] == id_emp]
    # convert timestamp to datetime format
    df_name["Timestamp"] = pd.to_datetime(df_name["Timestamp"])
    date_limit = date_limit if date_limit is not None else df["Timestamp"].max()
    # filter by max date
    df_name = df_name[df_name["Timestamp"] <= date_limit]
    # count the number of days when the person is atraso in event column
    df_atraso = df_name[df_name["Evento"] == "atraso"]
    days_late = (len(df_atraso), sum(df_atraso["Valor"]))
    # count the number of days when the person is extra in event column
    df_extra = df_name[df_name["Evento"] == "extra"]
    days_extra = (len(df_extra), sum(df_extra["Valor"]))
    # count the number of days when the person is falta in event column
    df_falta = df_name[df_name["Evento"] == "falta"]
    days_falta = (len(df_falta), sum(df_falta["Valor"]))
    # count the number of days when the person is prima in event column
    df_prima = df_name[df_name["Evento"] == "prima"]
    days_prima = (len(df_prima), sum(df_prima["Valor"]))
    # count the number of days when the person is normal in event column
    df_normal = df_name[df_name["Evento"] == "normal"]
    normals = (len(df_normal), sum(df_normal["Valor"]))
    df_early = df_name[df_name["Evento"] == "early"]
    earlies = (len(df_early), sum(df_early["Valor"]))
    df_pasive = df_name[df_name["Evento"] == "pasiva"]
    pasives = (len(df_pasive), sum(df_pasive["Valor"]))
    # generate tuple containing (timestamp, comment, value) for each event
    faltas = []
    for i, val in enumerate(df_falta["Timestamp"]):
        faltas.append((val, df_falta["Comentario"].iloc[i], df_falta["Valor"].iloc[i]))
    extras = []
    for i, val in enumerate(df_extra["Timestamp"]):
        extras.append((val, df_extra["Comentario"].iloc[i], df_extra["Valor"].iloc[i]))
    primas = []
    for i, val in enumerate(df_prima["Timestamp"]):
        primas.append((val, df_prima["Comentario"].iloc[i], df_prima["Valor"].iloc[i]))
    lates = []
    for i, val in enumerate(df_atraso["Timestamp"]):
        lates.append((val, df_atraso["Comentario"].iloc[i], df_atraso["Valor"].iloc[i]))
    normals = []
    for i, val in enumerate(df_normal["Timestamp"]):
        normals.append(
            (val, df_normal["Comentario"].iloc[i], df_normal["Valor"].iloc[i])
        )
    early = []
    for i, val in enumerate(df_early["Timestamp"]):
        early.append((val, df_early["Comentario"].iloc[i], df_early["Valor"].iloc[i]))
    contract = df_name["Contrato"].iloc[0] if len(df_name) > 0 else "NA"
    pasive = []
    for i, val in enumerate(df_pasive["Timestamp"]):
        pasive.append(
            (val, df_pasive["Comentario"].iloc[i], df_pasive["Valor"].iloc[i])
        )
    return (
        days_falta,
        days_extra,
        days_prima,
        days_late,
        faltas,
        extras,
        primas,
        lates,
        normals,
        early,
        pasive,
        contract,
    )


def get_info_o_file_name(
    contracts, name: str, id_2=None, flag=False
) -> tuple[str, list, list, list, float, list]:
    if flag:
        id_2, name_db = get_name_id_contracts(contracts, name)
        if id_2 is not None:
            for contract in contracts.keys():
                ids = []
                for emp_name in contracts[contract].keys():
                    ids.append((contracts[contract][emp_name]["id"], emp_name))
                emp, id_emp, flag = compare_employee_name(ids, id_2)
                if flag:
                    faltas = []
                    retardos = []
                    extras = []
                    primas = []
                    for i, state in enumerate(contracts[contract][emp]["status"]):
                        if state == "FALTA":
                            faltas.append(
                                (
                                    contracts[contract][emp]["fechas"][i],
                                    contracts[contract][emp]["comments"][i],
                                )
                            )
                        elif state == "RETARDO":
                            retardos.append(
                                (
                                    contracts[contract][emp]["fechas"][i],
                                    contracts[contract][emp]["comments"][i],
                                )
                            )
                    total_extra = 0.0
                    for i, val in enumerate(contracts[contract][emp]["extras"]):
                        if val != 0 and i <= 30:
                            extras.append(
                                (
                                    contracts[contract][emp]["fechas"][i],
                                    contracts[contract][emp]["comments"][i],
                                    val,
                                )
                            )
                            total_extra += val
                    for i, txt_prima in enumerate(contracts[contract][emp]["primas"]):
                        if "PRIMA" in txt_prima:
                            primas.append(
                                (
                                    contracts[contract][emp]["fechas"][i],
                                    contracts[contract][emp]["comments"][i],
                                )
                            )
                    return contract, faltas, retardos, extras, total_extra, primas
                else:
                    print(f"user not registered in the file OCT: {id_2}")
                    return "None", [], [], [], 0.0, []
        else:
            return "None", [], [], [], 0.0, []
    else:
        print("no data avaliable")
        return "None", [], [], [], 0.0, []


def divide_pairs(files_pairs: list):
    oct_files = []
    ternium_files = []
    for item in files_pairs:
        if "OCT" in item:
            oct_files.append(item)
        elif "Ternium" in item:
            ternium_files.append(item)
    return oct_files, ternium_files


def get_list_files(
    files, filename=None
) -> tuple[tuple[list[Any], list[Any]], list[Any]]:
    files_pairs = []
    files_names_f = []
    if filename is None:
        for k, v in files.items():
            if "Fichaje" in v["report"]:
                files_names_f.append(k)
        if len(files_names_f) > 0:
            selected = files_names_f[0]
            for k, v in files.items():
                if k == selected:
                    files_pairs = (
                        v["pairs"] if v["pairs"] is not None else ["No pair avaliable"]
                    )
    else:
        for k, v in files.items():
            if "Fichaje" in v["report"]:
                files_names_f.append(k)
                if k == filename:
                    files_pairs = (
                        v["pairs"] if v["pairs"] is not None else ["No pair avaliable"]
                    )
    files_pairs = divide_pairs(files_pairs)
    return files_pairs, files_names_f


def write_log_file(paths: list | str, text, username_data=None):
    time_zone = pytz.timezone(timezone_software)
    date = datetime.now(pytz.utc).astimezone(time_zone).strftime(format_date)
    paths = paths if isinstance(paths, list) else [paths]
    for path in paths:
        with open(f"{path}_log_{date}.txt", "a") as f:
            f.write(f"-->{text}" + "\n")
    return True


def get_cache_notifications(path: str):
    try:
        with open(path, "rb") as file:
            notifications = pickle.load(file)
        return notifications
    except Exception as e:
        print(f"Error at opening file notifications {e} {path}")
        notifications = {}
    return notifications


def update_cache_notifications(path: str, notifications: dict):
    try:
        with open(path, "wb") as file:
            pickle.dump(notifications, file)
        return True
    except Exception as e:
        print(f"Error at opening file notifications {e}")
        notifications = {}
        return False


def get_data_encuesta(file_path: str):
    if file_path.endswith(".xls") or file_path.endswith(".xlsx"):
        # open Excel file
        skip_rows = []
        cols = [0, 1, 2]
        warnings.simplefilter("ignore")
        # noinspection PyTypeChecker
        df = pd.read_excel(file_path)
    else:
        # open a csv file
        df = pd.read_csv(file_path)
    data = df.to_dict("records")
    return data, df


def extract_data_encuesta(data: list, type_q=2):
    data_out = []
    path_quizz = quizzes_RRHH[str(type_q)]["path"]
    dict_quizz_list = []
    metadata_list = []
    starts_withnumbers_pattern = "\d+\."
    for record_dict in data:
        metadata = {}
        dict_quizz = json.load(open(path_quizz, encoding="utf-8"))
        for key in record_dict.keys():
            if "[Puntuación]" in key or "[Comentarios]" in key:
                continue
            match = re.findall(starts_withnumbers_pattern, key)
            if not match:
                metadata[key] = record_dict[key]
            else:
                number = int(match[0].replace(".", ""))
                for k, v in dict_quizz.items():
                    items_list = v["items"]
                    if isinstance(items_list, str):
                        continue
                    elif isinstance(items_list, list):
                        range_items = range(items_list[0], items_list[1] + 1)
                        answers = (
                            v["answer"]
                            if isinstance(v["answer"], list)
                            else [[i, 0] for i in range(len(list(range_items)))]
                        )
                        if number not in range_items:
                            continue
                        options = v["options"]
                        options = [op.title() for op in options]
                        value = record_dict[key]
                        if (
                            value.lower() in options
                            or value.upper() in options
                            or value.title() in options
                            or value in options
                        ):
                            index = range_items.index(number)
                            index_val = options.index(value.title())
                            answers[index] = [index, index_val]
                        else:
                            index = range_items.index(number)
                            answers[index] = [index, 0]
                        dict_quizz[k]["answer"] = answers
                        break
        # for k, v in dict_quizz.items():
        #     items = v["items"]
        #     if isinstance(items, str):
        #         continue
        #     elif isinstance(items, list):
        #         range_items = range(items[0], items[1] + 1)
        #         answers = (
        #             v["answer"]
        #             if isinstance(v["answer"], list)
        #             else [[i, 0] for i in range(len(list(range_items)))]
        #         )
        #         v["answer"] = answers
        dict_quizz_list.append(dict_quizz)
        metadata_list.append(metadata)
    return dict_quizz_list, metadata_list


class Norm35Formatter:
    def __init__(self, type_q):
        dict_conversions = json.load(open(conversion_quizzes_path, encoding="utf-8"))
        match type_q:
            case 1:
                self.dict_categories = dict_conversions["norm035"]["v1"]["categorias"]
            case 2:
                self.dict_categories = dict_conversions["norm035"]["v2"]["categorias"]

    def get_categories(self):
        categories = []
        for k, v in self.dict_categories.items():
            categories.append((k, v["categoria"], v["dominio"]))
        return categories

    def get_category_data(self, category_name):
        for k, v in self.dict_categories.items():
            if v["categoria"] == category_name:
                return k, v["categoria"], list(v["dominio"].keys())
        return None, None, None

    def get_category_data_by_key(self, keyword):
        if keyword in self.dict_categories.keys():
            return (
                keyword,
                self.dict_categories[keyword]["categoria"],
                list(self.dict_categories[keyword]["dominio"].keys()),
            )
        return None, None, None

    def get_dominio_data(self, cat_key, dominio):
        if cat_key in self.dict_categories.keys():
            if dominio in self.dict_categories[cat_key]["dominio"].keys():
                return self.dict_categories[cat_key]["dominio"][dominio]["dimensiones"]
        return None


def create_report_encuesta(metadata_list: dict, type_q: int, dict_results_list) -> str:
    norm35 = Norm35Formatter(type_q)

    columns = [
        "Total",
        "Categoria",
        "Puntos",
        "Dominio",
        "Puntos",
        "Dimension",
        "Puntos",
    ]
    path_out = "files/quizz_out/report_norm35.xlsx"
    nips = []
    dfs = []
    for index, dict_results in enumerate(dict_results_list):
        data_page = []
        row = [0, "", 0, "", 0, "", 0]
        c_final = dict_results["c_final"]
        c_categoria = dict_results["c_cat"]
        c_dominio_dict = dict_results["c_dom"]
        c_dimension_dict = dict_results["c_dim"]
        row[0] = c_final
        for category, v in c_categoria.items():
            row[1] = category
            row[2] = v
            key_cat = norm35.get_category_data(category)[0]
            for dominio, v1 in c_dominio_dict.items():
                row[3] = dominio
                row[4] = v1
                dom_data = norm35.get_dominio_data(key_cat, dominio)
                if dom_data is None:
                    continue
                for dimension, v2 in c_dimension_dict.items():
                    row[5] = dimension
                    row[6] = v2
                    dimensions = [dim_dic["dimension"] for dim_dic in dom_data]
                    if dimension in dimensions:
                        data_page.append(row.copy())
        df = pd.DataFrame(data_page, columns=columns)
        nip_encuesta = metadata_list[index]["NIP Encuesta:"]
        nip_encuesta = nip_encuesta.replace("*", "")
        dfs.append(df)
        nips.append(nip_encuesta)
    # save as excel
    with pd.ExcelWriter(path_out, engine="xlsxwriter", mode="w") as writer:
        for index, df in enumerate(dfs):
            df.to_excel(writer, sheet_name=f"{nips[index]}", index=False)
    return path_out
