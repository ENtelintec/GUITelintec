# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:37 $'

import csv
import json
import os
import pickle
import re
import warnings
from calendar import monthrange
from datetime import datetime
from tkinter import Misc, Frame, messagebox
from tkinter.ttk import Frame
from typing import Tuple, Dict, Any

import dropbox
import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification

from static.extensions import secrets, cache_oct_file_temp_path, cache_oct_fichaje_path
from templates.Functions_SQL import get_id_employee, get_all_fichajes, get_employee_id_name, update_fichaje_DB, \
    insert_new_fichaje_DB
from templates.Functions_Text import clean_accents, compare_employee_name


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
            dbx = dropbox.Dropbox(secrets['APP_DROPBOX_TOKEN'])
            print("Exploring: ", fname)
            data = dbx.files_list_folder(path=fname)
            for entry in data.entries:
                if hasattr(entry, 'shared_folder_id'):
                    folders.append(entry.name) if not check_only_read_conflict(entry.name) else None
                else:
                    files.append(entry.name) if not check_only_read_conflict(entry.name) else None
        except Exception as e:
            print(e)
            print('Error dropbox')
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
            print('Error local')
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
            local_file = 'files/folders_' + item + local_name + '.pkl'
            fdir = father + "/" + rpaths[item]
            directory = map_dropbox_folders(fdir, online=online)
            with open(local_file, 'wb') as f:
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
            local_file = 'files/folders_' + item + local_name + '.pkl'
            with open(local_file, 'rb') as f:
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
        local_file = 'files/folders_' + item + local_name + '.pkl'
        with open(local_file, 'wb') as f:
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


def validate_digits_numbers(new_value) -> bool:
    """
    Validates that the new value is a number.
    This function is called when the user types in a new value in the
    spinbox.
    It checks if the new value is a number and returns True or
    False accordingly.
    :param new_value: New value to be validated
    :return: True if the new value is a number, False otherwise
    """
    return new_value.isdigit()


def create_spinboxes_time(master: Misc, father, row: int, column: int,
                          pad_x: int = 5, pad_y: int = 5,
                          style: str = 'primary', title: str = "",
                          mins_defaul=0, hours_default=8) -> tuple[Frame, dict[Any, Any]]:
    """ Creates a clock with two spinboxes for minutes and hours
    :param title:
    :param father:
    :param master: <Misc> father instance where the object is created
    :param row: <int> row to be placed
    :param column: <int> column to be placed
    :param pad_x: <int> pad in x for the group, not for individual object
    :param pad_y: <int> pad in y for the group, not for individual object
    :param style: <str> bootstrap style selected
    :param mins_defaul: <int> default value for minutes
    :param hours_default: <int> deafult value for hours
    :return: Frame tkinter frame containing the spinboxes
    """
    clock = ttk.Frame(master)
    clock.grid(row=row, column=column, padx=pad_x, pady=pad_y, sticky="w")
    # minutes spinboxes
    # noinspection PyArgumentList
    minutes_spinbox = ttk.Spinbox(clock, from_=0, to=59, bootstyle=style,
                                  width=2, justify="center")
    minutes_spinbox.grid(row=0, column=1, padx=1, pady=1, sticky="w")
    # hours spinbox
    # noinspection PyArgumentList
    hours_spinbox = ttk.Spinbox(clock, from_=0, to=23, bootstyle=style,
                                width=2, justify="center")
    hours_spinbox.grid(row=0, column=0, padx=1, pady=1, sticky="w")
    # add valitation to spinbox
    vcmd_mins = (master.register(validate_digits_numbers), '%P')
    minutes_spinbox.configure(validate="key", validatecommand=vcmd_mins)
    vcmd_hours = (master.register(validate_digits_numbers), '%P')
    hours_spinbox.configure(validate="key", validatecommand=vcmd_hours)
    # set default values
    minutes_spinbox.set(mins_defaul)
    hours_spinbox.set(hours_default)
    # father.clocks.append({title: [minutes_spinbox, hours_spinbox]})
    return clock, {title: [minutes_spinbox, hours_spinbox]}


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
        status, fechas, comments, extras, primas, in_door,
        out_door) -> tuple[list, list, list, list, list, list, list]:
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


def get_data_from_cache_sheet(filepath: str, excel_file, sheet: str, inital_skip_rows) -> list | None:
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
    with open(filepath, mode="r",
              encoding='utf-8') as csv_file:  # "r" represents the read mode
        reader = csv.reader(csv_file)  # this is the reader object
        for item in reader:
            data.append(item)
    return data


def get_data_from_sliced(data_aux) -> tuple[list, list, list, list, list, list, list, str]:
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
        with open(filepath, 'rb') as f:
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
            data = get_data_from_cache_sheet(cache_oct_file_temp_path, excel_file, sheet, inital_skip_rows)
            if data is None:
                continue
            contracts[sheet] = {} if sheet not in contracts.keys() else contracts[sheet]
            indexes = range(len(data))
            starting_indexes = [indexes[i] for i in range(0, len(indexes), 4)]
            data_sliced = [data[i:i + 4] for i in starting_indexes]
            try:
                for data_aux in data_sliced:
                    status, fechas, comments, extras, primas, in_door, out_door, name = get_data_from_sliced(data_aux)
                    if name != "":
                        status, fechas, comments, extras, primas, in_door, out_door = clean_data_contract(
                            status, fechas, comments, extras, primas, in_door, out_door)
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
                messagebox.showerror(
                    "Error", f"Error al leer la pagina. {sheet}\n"
                             " Asegurese sea el archivo correcto, con el formato correcto.\n" + str(e))
                continue
    except Exception as e:
        print(e)
        messagebox.showerror("Error",
                             "Error al leer el archivo.\n"
                             " Asegurese sea el archivo correcto, con el formato correcto.\n" + str(e)
                             )
    with open(cache_oct_fichaje_path, 'wb') as file:
        pickle.dump(contracts, file)
    if len(bad_names) > 0:
        msg = "Se han encontrado los siguientes empleados no registrados:\n"
        for ename in bad_names:
            msg += ename + "\n"
        messagebox.showinfo("Error", msg)
        toast = ToastNotification(
            title="Error en nombres",
            message=msg,
            duration=8000,
        )
        toast.show_toast()
    return contracts


def get_name_id_contracts(contracts: dict, name: str) -> tuple[Any, str] | tuple[None, str]:
    """
    Gets the name and id of an employee from a dictionary.
    :param contracts:
    :param name:
    :return:
    """
    for contract in contracts.keys():
        for emp in contracts[contract].keys():
            if name.lower() == contracts[contract][emp]["name_db"].lower() or name.lower() == emp.lower():
                return contracts[contract][emp]["id"], contracts[contract][emp]["name_db"]
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
                    table_data.append([con_name, emp_name,
                                       contracts[con_name][emp_name]["id"],
                                       contracts[con_name][emp_name]["fechas"][i],
                                       clean_status_contracts(contracts[con_name][emp_name]["status"][i]),
                                       contracts[con_name][emp_name]["extras"][i],
                                       contracts[con_name][emp_name]["primas"][i],
                                       contracts[con_name][emp_name]["in_door"][i],
                                       contracts[con_name][emp_name]["out_door"][i],
                                       contracts[con_name][emp_name]["comments"][i]])
    columns = ["Contrato", "Empleado", "ID", "Fecha", "Status", "Extras", "Primas", "Entrada",
               "Salida", "Comentarios"]
    return table_data, columns


def extract_fichajes_file(filename: str):
    """
    Extracts the data from a file
    :param filename:
    :return:
    """
    try:
        skip_rows = [0, 1, 2]
        cols = [0, 1, 2] if "Ternium" in filename else [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        warnings.simplefilter("ignore")
        # noinspection PyTypeChecker
        df = pd.read_excel(filename, skiprows=skip_rows, usecols=cols)
        if "Ternium" in filename:
            df.dropna(inplace=True)
            df["Fecha/hora"] = clean_date(df["Fecha/hora"].tolist())
            df["Fecha/hora"] = pd.to_datetime(df["Fecha/hora"], format="mixed", dayfirst=True)
            df.dropna(subset=['Fecha/hora'], inplace=True)
            df["status"], df["name"], df["card"], df["in_out"] = clean_text(
                df["Texto"].to_list())
            df["in_out"] = clean_in_out(df["in_out"].tolist())
        else:
            df.dropna(inplace=True)
            df = df[df["Fecha de fichaje a la entrada"] != "--"]
            df = df[df["Fecha de fichaje a la salida"] != "--"]
            df["Fecha/hora_in"] = df["Fecha de fichaje a la entrada"] + " " + df[
                "Hora de fichaje a la entrada"]
            df.drop(columns=["Fecha de fichaje a la entrada",
                             "Hora de fichaje a la entrada"], inplace=True)
            df["Fecha/hora_out"] = df["Fecha de fichaje a la salida"] + " " + df[
                "Hora de fichaje a la salida"]
            df.drop(columns=["Fecha de fichaje a la salida",
                             "Hora de fichaje a la salida"], inplace=True)
            df["Fecha/hora_in"] = pd.to_datetime(df["Fecha/hora_in"], format="mixed", dayfirst=True)
            df["Fecha/hora_out"] = pd.to_datetime(df["Fecha/hora_out"], format="mixed", dayfirst=True)
            df["Fecha"] = pd.to_datetime(df["Fecha"], format="mixed", dayfirst=True)
            df["name"] = df["Nombre"].str.upper() + " " + df["Apellido"].str.upper()
            df["Horas trabajadas"] = transform_hours_to_float(df["Horas trabajadas"].tolist())
            df.drop(columns=["Nombre", "Apellido"], inplace=True)
        return df
    except Exception as e:
        messagebox.showerror("Error",
                             "Error al leer el archivo.\n Asegurese sea el archivo correcto, con el formato correcto.")
        print(e)
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
        return self.name + ' ' + str(self.father) + ' ' + str(len(self.children)) + ' ' + str(len(self.files))

    def __repr__(self):
        return self.name


def remove_extensions(files: list):
    """
    Removes the extensions from the files
    :param files:
    :return:
    """
    for i, file in enumerate(files):
        files[i] = file.split(".")[0]
    return files


def get_metadata_file(path: str, file: str):
    """
    Gets the metadata from the file (empresa)_(date).ext.
    The dictionary contains the path, extension, size, report, date.
    The report and date are empty if the file is not a fichaje file.
    The date is in the format yyyy-mm-dd.
    The report is the first word before the date.
    The date is the second word before the date.
    The report and date are empty if the file is not a fichaje file.
    :param path: Parent path of the file
    :param file: Name of the file
    :return: dictionary of the file.
    {Path, extension, size, report, date}

    """
    out = {
        "path": path + file,
        "extension": file.split(".")[-1],
        "size": os.path.getsize(os.path.join(path, file)),
        "report": "",
        "date": "",
        "pairs": None
    }
    file = remove_extensions([file])[0]
    names = file.split("_")
    if len(names) > 1:
        out["report"] = names[0]
        out["date"] = names[1]
    return out


def check_files_pairs_date(files_data: dict) -> dict:
    """
    Checks if the files are pairs and if they are in the same month.
    :param files_data: Dictionary with the metadata of the files.
    :return: Dictionary update with the possible pairs.
    """
    for k in files_data.keys():
        if "Fichaje" not in k:
            continue
        pairs = []
        date1 = files_data[k]["date"]
        date1 = datetime.strptime(date1, '%d-%m-%Y')
        for k2 in files_data.keys():
            if "Fichaje" in k2:
                continue
            if k2 != k:
                date2 = files_data[k2]["date"]
                date2 = datetime.strptime(date2, '%d-%m-%Y')
                diff_dates = date1 - date2
                if 0 <= diff_dates.days <= 31 and date2 <= date1:
                    pairs.append(k2)
        files_data[k]["pairs"] = pairs if len(pairs) > 0 else None
    return files_data


def check_fichajes_files_in_directory(path: str, patterns: list) -> tuple[bool, dict]:
    """
    Checks if the files in the directory are a fichajes files
    The dictionary contains the path, extension, size, report, date.
    The report and date are empty if the file is not a fichaje file.
    The date is in the format yyyy-mm-dd.
    The report is the first word before the date.
    The date is the second word before the date.
    The report and date are empty if the file is not a fichaje file.
    The dictionary is empty if the files are not fichajes files.
    The boolean is False if the files are not fichajes files.
    The boolean is True if the files are a fichajes files.
    The dictionary is empty if the files are not fichajes files.
    The boolean is False if the files are not fichajes files.
    The boolean is True if the files are a fichajes files.
    The dictionary is empty if the files are not fichajes files.
    The boolean is False if the files are not fichajes files.
    :param patterns: Patterns to detect in the name
    :param path: path to the directory
    :return: tuple with the boolean and the dictionary with the metadata of the files.
    """
    files = os.listdir(path)
    files_data = {}
    for file in files:
        # check in file contains any pattern in the patterns list
        for pattern in patterns:
            if pattern in file:
                files_data[file] = get_metadata_file(path, file)
    if len(files_data) > 0:
        files_data = check_files_pairs_date(files_data)
    return False if len(files_data) == 0 else True, files_data


def get_dict_fichaje(dict_list: list[dict], data: list[dict]):
    for i, item_dict in enumerate(data):
        dict_f = dict_list[i]
        if item_dict is not None:
            for timestamp_key, item in item_dict.items():
                timestamp = datetime.strptime(timestamp_key, '%Y-%m-%d %H:%M:%S') if type(
                    timestamp_key) is str else timestamp_key
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
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
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
    days_missing_o, days_late_o, days_extra_o, primes_o, normal_o = (None, None, None, None, None)
    days_missing_t, days_late_t, days_extra_t, primes_t, normal_t = (None, None, None, None, None)
    days_missing_f, days_late_f, days_extra_f, primes_f, normal_f = data_fichaje
    for key, value in kwargs.items():
        if key == "oct_file":
            days_missing_o, days_late_o, days_extra_o, primes_o, normal_o = value
        elif key == "ternium_file":
            days_missing_t, days_late_t, days_extra_t, primes_t, normal_t = value
    dict_f = {}
    days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic = ({}, {}, {}, {}, {})
    days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic = get_dict_fichaje(
        [days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic],
        [days_missing_f, days_late_f, days_extra_f, primes_f, normal_t])
    days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic = get_dict_oct(
        [days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic],
        [days_missing_o, days_late_o, days_extra_o, primes_o, normal_o])
    days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic = get_dict_fichaje(
        [days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic],
        [days_missing_t, days_late_t, days_extra_t, primes_t, normal_t])
    return days_missing_dict, days_late_dict, days_extra_dict, primes_dict, normal_dic


def get_cumulative_data_fichajes_dict(dic_data: dict) -> tuple[int, int]:
    """
    Gets the cumulative data from a dictionary of data from fichajes files
    :param dic_data:
    :return:
    """
    total_days = 0
    total_value = 0
    for year in dic_data.keys():
        for month in dic_data[year].keys():
            total_days += len(dic_data[year][month].keys())
            for day in dic_data[year][month].keys():
                value = dic_data[year][month][day]["value"]
                if value is not None and value != "":
                    total_value += value
    return total_days, total_value


def update_fichajes_resume_cache(filepath: str, data, just_file=False, id_emp_up=None, deletion=False):
    """
    Updates the fichajes resume cache
    :param deletion:
    :param id_emp_up: id for update only one registry
    :param just_file:
    :param filepath:
    :param data:
    :return:
    """
    update = True
    try:
        with open(filepath, 'rb') as file:
            fichajes_resume = pickle.load(file)
    except Exception as e:
        print("Error at getting cache file to update: ", e)
        update = False
        fichajes_resume = data
    if update and not just_file and id_emp_up is None and not deletion:
        ids_old = [item[0] for item in fichajes_resume]
        ids_new = [item[0] for item in data]
        new_insert_ids = list(set(ids_new) - set(ids_old))
        for index_1, item_1 in enumerate(data):
            for index_0, item_0 in enumerate(fichajes_resume):
                id_new = item_1[0]
                id_old = item_0[0]
                if id_new == id_old and item_0[2] == item_1[2]:
                    (id_emp, name, contract, faltas, lates, total_lates, extras, total_extra, primas,
                     faltas_dic, lates_dic, extras_dic, primas_dic, normal_dic) = fichajes_resume[index_0]
                    (id_emp2, name2, contract2, faltas2, lates2, total_lates2, extras2, total_extra2, primas2,
                     faltas_dic2, lates_dic2, extras_dic2, primas_dic2, normal_dic2) = data[index_1]
                    faltas_dic.update(faltas_dic2)
                    lates_dic.update(lates_dic2)
                    extras_dic.update(extras_dic2)
                    primas_dic.update(primas_dic2)
                    normal_dic.update(normal_dic2)
                    new_faltas, new_faltas_value = get_cumulative_data_fichajes_dict(faltas_dic)
                    new_lates, new_lates_value = get_cumulative_data_fichajes_dict(lates_dic)
                    new_extras, new_extras_value = get_cumulative_data_fichajes_dict(extras_dic)
                    new_primas, new_primas_value = get_cumulative_data_fichajes_dict(primas_dic)
                    aux = (id_emp, name, contract, new_faltas, new_lates, new_extras, new_extras_value, new_primas,
                           faltas_dic, lates_dic, extras_dic, primas_dic, normal_dic)
                    flag, error, result = update_fichaje_DB(
                        id_new, contract, faltas_dic, lates_dic, extras_dic, primas_dic, normal_dic)
                    if flag:
                        print("Fichaje updated DB: ", id_emp)
                        fichajes_resume[index_0] = aux
                    else:
                        print("Error at updating DB")
                        print(error)
                    break
        for id_new in new_insert_ids:
            for item in data:
                (id_emp2, name2, contract2, faltas2, lates2, total_lates2, extras2, total_extra2, primas2,
                 faltas_dic2, lates_dic2, extras_dic2, primas_dic2, normal_dic2) = item
                if id_new == id_emp2:
                    aux = (id_new, name2, contract2, faltas2, lates2, total_lates2, extras2, total_extra2, primas2,
                           faltas_dic2, lates_dic2, extras_dic2, primas_dic2, normal_dic2)
                    flag, error, result = insert_new_fichaje_DB(id_new, contract2, faltas_dic2, lates_dic2, extras_dic2,
                                                                primas_dic2, normal_dic2)
                    if flag:
                        fichajes_resume.append(aux)
                        print("Fichaje added DB")
                    else:
                        print("Error at creating new registry at DB")
                        print(error)
                    break
    if just_file:
        fichajes_resume = data
    if id_emp_up is not None:
        ids_old = [item[0] for item in fichajes_resume]
        ids_new = [item[0] for item in data]
        if id_emp_up not in ids_old:
            for index_1, item_1 in data:
                (id_emp, name, contract, faltas, lates, total_lates, extras, total_extra, primas,
                 faltas_dic, lates_dic, extras_dic, primas_dic, normal_dic) = item_1
                if id_emp == id_emp_up:
                    flag, error, result = insert_new_fichaje_DB(id_emp, contract, faltas_dic, lates_dic, extras_dic,
                                                                primas_dic, normal_dic)
                    if flag:
                        fichajes_resume.append(item_1)
                        print("Fichaje added DB")
                    else:
                        print("Error at creating new registry at DB")
                        print(error)
                    break
        else:
            for index_1, item_1 in enumerate(data):
                (id_emp, name, contract2, faltas2, lates2, total_lates2, extras2, total_extra2, primas2,
                 faltas_dic2, lates_dic2, extras_dic2, primas_dic2, normal_dic2) = item_1
                if id_emp_up == id_emp:
                    for index_0, item_0 in enumerate(fichajes_resume):
                        if id_emp == item_0[0]:
                            (id_emp_0, name, contract, faltas, lates, total_lates, extras, total_extra, primas,
                             faltas_dic, lates_dic, extras_dic, primas_dic, normal_dic) = fichajes_resume[index_0]
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
                            new_faltas, new_faltas_value = get_cumulative_data_fichajes_dict(faltas_dic)
                            new_lates, new_lates_value = get_cumulative_data_fichajes_dict(lates_dic)
                            new_extras, new_extras_value = get_cumulative_data_fichajes_dict(extras_dic)
                            new_primas, new_primas_value = get_cumulative_data_fichajes_dict(primas_dic)
                            aux = (id_emp, name, contract,
                                   new_faltas, new_lates, new_lates_value, new_extras, new_extras_value, new_primas,
                                   faltas_dic, lates_dic, extras_dic, primas_dic, normal_dic)
                            flag, error, result = update_fichaje_DB(
                                id_emp, contract, faltas_dic, lates_dic, extras_dic, primas_dic, normal_dic)
                            if flag:
                                print(f"Fichaje updated DB: {id_emp}")
                                fichajes_resume[index_0] = aux
                            else:
                                print("Error at updating DB")
                                print(error)
                            break
                    break
    with open(filepath, 'wb') as file:
        pickle.dump(fichajes_resume, file)
    print("Fichajes resume cache file rewrited")


def get_fichajes_resume_cache(filepath, hard_update=False) -> tuple[list, bool]:
    """
    Gets the fichajes resume cache if exists else the data is obtained from the
    db, and then the cumulative values of absences, delays, extra hours and primes
    are calculated.
    :param hard_update:
    :param filepath:
    :return:
    """
    fichajes_resume = []
    flag = False
    if hard_update:
        try:
            with open(filepath, 'rb') as file:
                fichajes_resume = pickle.load(file)
            flag = False if len(fichajes_resume) == 0 or fichajes_resume is None else True
        except Exception as e:
            print("Error at getting cache file: ", e)
            fichajes_resume = []
            flag = False
    else:
        flag = False
    if not flag:
        "calling db, because file not founded"
        flag, error, result = get_all_fichajes()
        if flag and len(result) > 0:
            fichajes_resume = []
            for row in result:
                (name, lastname, id_fich, id_emp, contract, absences, lates, extras, primes, normal) = row
                new_faltas, new_faltas_value = get_cumulative_data_fichajes_dict(json.loads(absences))
                new_tardanzas, new_tardanzas_value = get_cumulative_data_fichajes_dict(json.loads(lates))
                new_extras, new_extras_value = get_cumulative_data_fichajes_dict(json.loads(extras))
                new_primas, new_primas_value = get_cumulative_data_fichajes_dict(json.loads(primes))
                new_row = (id_emp, name.title() + lastname.title(), contract,
                           new_faltas, new_faltas_value, new_tardanzas,
                           new_extras, new_extras_value, new_primas,
                           json.loads(absences), json.loads(lates),
                           json.loads(extras), json.loads(primes), json.loads(normal))
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
        with open(filepath, 'rb') as file:
            data = pickle.load(file)
        flag = False if len(data) == 0 else True
    except Exception as e:
        print("Error at getting cache file: ", e)
        data = {}
        flag = False
    return data, flag


def update_fichajes_emp_cache(filepath: str, data: dict):
    """
    Updates the fichajescache file with the data provided. If the file does not exist
    it is created. If the file exists, it is updated.
    :param filepath:
    :param data:
    :return:
    """
    with open(filepath, 'wb') as file:
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
    with open(filepath, 'r') as file:
        content = file.readlines()
        for item in content:
            out.append(tuple(item.split(',;')))
    return out


def get_ExMed_cache_file(filepath: str) -> tuple[bool, dict]:
    """
    Gets the ExMed cache file if exists.
    :param filepath:
    :return:
    """
    try:
        with open(filepath, 'rb') as file:
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
    with open(filepath, 'wb') as file:
        pickle.dump(data, file)
    return True, None


def open_file_settings(filepath: str) -> tuple[bool, dict]:
    """
    Opens the json settings file.
    :param filepath:
    :return:
    """
    flag = False
    settings = {}
    if not os.path.exists(filepath):
        return flag, settings
    # Open the file and read the data.
    with open(filepath, 'r') as file:
        settings = json.load(file)
    flag = True
    return flag, settings


def update_file_settings(filepath: str, settings: dict):
    """
    Updates the json settings file.
    :param filepath:
    :param settings:
    :return:
    """
    # Open the file and read the data.
    if not os.path.exists(filepath):
        with open(filepath, 'w') as file:
            json.dump(settings, file)
        return True, None
    # Open the file and read the data.
    with open(filepath, 'r') as file:
        data = json.load(file)
    data.update(settings)
    # Open the file and write the data.
    with open(filepath, 'w') as file:
        json.dump(data, file)
    return True, None


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
    n_days_month = monthrange(date.year, date.month)
    days_of_the_month = [i for i in range(1, n_days_month[1] + 1)]
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


def get_worked_days(df_name: pd.DataFrame):
    days_worked = df_name["Fecha"].tolist()
    last_date = days_worked[-1] if len(days_worked) > 0 else None
    days_for_work = []
    if last_date is None:
        return [], []
    days_for_work = get_days_work(last_date)
    for day_worked in days_worked:
        if day_worked.day in days_for_work:
            days_for_work.remove(day_worked.day)
    days_not_worked = get_date_from_days_list(last_date, days_for_work)
    days_worked = df_name[["Fecha", "Horas trabajadas", "Dispositivo de fichaje de entrada", "Dispositivo de fichaje de salida"]].values.tolist()
    return days_worked, days_not_worked


def get_info_f_file_name(df: pd.DataFrame, name: str, clocks, window_time_in, window_time_out, flag):
    if flag:
        df_name = df[df["name"] == name]
        df_name_in = df[df["name"] == name]
        days_worked, days_not_worked = get_worked_days(df_name)
        min_in = clocks[0]["entrada"][0].get()
        hour_in = clocks[0]["entrada"][1].get()
        min_out = clocks[1]["salida"][0].get()
        hour_out = clocks[1]["salida"][1].get()
        # filter worked days within monday and saturday
        df_name_in.set_index('Fecha/hora_in', inplace=True)
        # filter late days and extra hours
        # set entrance hour
        aux_hour = int(hour_in) + int(window_time_in.get() / 60)
        aux_min = int(min_in) + int(window_time_in.get() % 60)
        limit_hour = pd.Timestamp(year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0)
        # count the number of rows where the person is late
        late_name = df_name[df_name["Fecha/hora_in"].dt.time > limit_hour.time()]
        count_late = len(late_name)
        # calculate the time difference between the entrance hour and the limit hour
        late_dic = {}
        for i in late_name[["Fecha/hora_in", "Dispositivo de fichaje de entrada"]].values:
            time_str = pd.Timestamp(year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=0)
            late_dic[i[0]] = (time_str - limit_hour, i[1])
        # filter extra hours
        # set exit hour
        aux_hour = int(hour_out) + int(window_time_out.get() / 60)
        aux_min = int(min_out) + int(window_time_out.get() % 60)
        limit_hour = pd.Timestamp(year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0)
        # count the number of rows where the person is late
        extra_name = df_name[df_name["Fecha/hora_out"].dt.time > limit_hour.time()]
        count_extra = len(extra_name)
        # calculate the time difference between the entrance hour and the late hour
        extra_dic = {}
        for i in extra_name[["Fecha/hora_out", "Dispositivo de fichaje de salida"]].values:
            time_str = pd.Timestamp(year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=0)
            extra_dic[i[0]] = (time_str - limit_hour, i[1])
        return days_worked, days_not_worked, count_late, count_extra, late_dic, extra_dic


def get_info_t_file_name(df: pd.DataFrame, name: str, clocks, window_time_in, window_time_out, flag):
    if flag:
        df_name = df[df["name"] == name]
        df_name_entrada = df_name[df_name["in_out"] == "DENTRO"]
        df_name_salida = df_name[df_name["in_out"] == "FUERA"]
        worked_days = len(df_name["name"].to_list())
        min_in = clocks[0]["entrada"][0].get()
        hour_in = clocks[0]["entrada"][1].get()
        min_out = clocks[1]["salida"][0].get()
        hour_out = clocks[1]["salida"][1].get()
        # filter worked days
        df_name.set_index('Fecha/hora', inplace=True)
        worked_intime = len(
            df_name.between_time(start_time=f"{hour_in}:{min_in}:00", end_time=f"{hour_out}:{min_out}:00"))
        # filter late days and extra hours
        # set entrance hour
        aux_hour = int(hour_in) + int(window_time_in.get() / 60)
        aux_min = int(min_in) + int(window_time_in.get() % 60)
        limit_hour = pd.Timestamp(year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0)
        # count the number of rows where the person is late
        late_name = df_name_entrada[df_name_entrada["Fecha/hora"].dt.time > limit_hour.time()]
        count = len(late_name)
        # calculate the time difference between the entrance hour and the late hour
        time_late = {}
        for i in late_name[["Fecha/hora", "Puerta"]].values:
            time_str = pd.Timestamp(year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=i[0].second)
            diff = time_str - limit_hour
            time_late[i[0]] = (diff, i[1])
        # calculate the number of days when the person worked extra hours
        aux_hour = int(hour_out) + int(window_time_out.get() / 60)
        aux_min = int(min_out) + int(window_time_out.get() % 60)
        limit_hour2 = pd.Timestamp(year=1, month=1, day=1, hour=aux_hour, minute=aux_min, second=0)
        extra_name = df_name_salida[df_name_salida["Fecha/hora"].dt.time > limit_hour2.time()]
        count2 = len(extra_name)
        extra_time = {}
        for i in extra_name[["Fecha/hora", "Puerta"]].values:
            time_str = pd.Timestamp(year=1, month=1, day=1, hour=i[0].hour, minute=i[0].minute, second=i[0].second)
            diff = time_str - limit_hour2
            extra_time[i[0]] = (diff, i[1])
        return worked_days, worked_intime, count, count2, time_late, extra_time
    else:
        return "NA", "NA", "NA", "NA", {}, {}


def get_info_bitacora(df: pd.DataFrame, name: str, id_emp: int, flag):
    if flag:
        df_name = df[df["ID"] == id_emp]
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
            normals.append((val, df_normal["Comentario"].iloc[i], df_normal["Valor"].iloc[i]))
        contract = df_name["Contrato"].iloc[0] if len(df_name) > 0 else "NA"
        return (days_falta, days_extra, days_prima, days_late,
                faltas, extras, primas, lates, normals, contract)

    else:
        return 0.0, 0.0, 0.0, 0.0, [], [], [], []


def get_info_o_file_name(contracts, name: str, id_2=None, flag=False) -> tuple[str, list, list, list, float, list]:
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
                            faltas.append((contracts[contract][emp]["fechas"][i],
                                           contracts[contract][emp]["comments"][i]))
                        elif state == "RETARDO":
                            retardos.append((contracts[contract][emp]["fechas"][i],
                                             contracts[contract][emp]["comments"][i]))
                    total_extra = 0.0
                    for i, val in enumerate(contracts[contract][emp]["extras"]):
                        if val != 0 and i <= 30:
                            extras.append((contracts[contract][emp]["fechas"][i],
                                           contracts[contract][emp]["comments"][i],
                                           val))
                            total_extra += val
                    for i, txt_prima in enumerate(contracts[contract][emp]["primas"]):
                        if "PRIMA" in txt_prima:
                            primas.append((contracts[contract][emp]["fechas"][i],
                                           contracts[contract][emp]["comments"][i]))
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


def get_list_files(files, filename=None) -> tuple[tuple[list[Any], list[Any]], list[Any]]:
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
                    files_pairs = v["pairs"] if v["pairs"] is not None else ["No pair avaliable"]
    else:
        for k, v in files.items():
            if "Fichaje" in v["report"]:
                files_names_f.append(k)
                if k == filename:
                    files_pairs = v["pairs"] if v["pairs"] is not None else ["No pair avaliable"]
    files_pairs = divide_pairs(files_pairs)
    return files_pairs, files_names_f


def write_log_file(path, text):
    with open(f"{path}bitacora_log.txt", "a") as f:
        f.write(text + "\n")
    return True
