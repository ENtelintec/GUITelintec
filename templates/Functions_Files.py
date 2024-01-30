# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:37 $'

import csv
import json
import os
import pickle
import re
from datetime import datetime
from tkinter import Misc, Frame, messagebox
from tkinter.ttk import Treeview

import dropbox
import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.toast import ToastNotification

from static.extensions import secrets
from templates.Functions_SQL import get_id_employee, get_all_fichajes
from templates.Functions_Text import clean_accents


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


def create_visualizer_treeview(master: Misc, table: str, rows: int,
                               pad_x: int = 5, pad_y: int = 10,
                               row: int = 0, column: int = 0,
                               style: str = 'primary',
                               headers=None, data=None) -> Treeview | None:
    """
    Creates a treeview with the given table and data
    :param style: ttkbootstrap style
    :param data: data for the rows
    :param headers: column headers
    :param table: Type of table to be created (fichajes, etc.)
    :param column: <int> column to be placed
    :param row: <int> row to be placed
    :param pad_x: <int> pad in x for the group, not the treeview
    :param pad_y: <int> pad in y for the group, not the treeview
    :param rows: <int> number of rows for the treeview
    :param master: <Misc> father instance where the object is created
    :return: treeview
    """
    match table:
        case "fichajes":
            columns = headers if headers is not None else ["Timestamp", 'Puerta', 'Texto', 'Status', 'Name', 'Card',
                                                           'in_out']
            heading_width = [25, 100, 100, 100, 100, 100, 100, 200]
            data = data if data is not None else [None, None, None, None, None, None, None]
        case _:
            columns = []
            data = []
            heading_width = []
            print("Error in create_visualizer_treeview")
    column_span = len(columns)
    # noinspection PyArgumentList
    treeview = ttk.Treeview(master, columns=columns, show="headings",
                            height=rows, bootstyle=style)
    for i in range(column_span):
        treeview.column(columns[i], width=heading_width[i])
        treeview.heading(columns[i], text=columns[i])
    treeview.grid(row=row, column=column, padx=pad_x, pady=pad_y,
                  columnspan=column_span, sticky="w")
    for entry in data:
        treeview.insert("", "end", values=entry)
    return treeview


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
                          mins_defaul=0, hours_default=8) -> Frame | None:
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
    father.clocks.append({title: [minutes_spinbox, hours_spinbox]})
    return clock


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


def clean_data_contract(status, fechas, comments, extras, primas, in_door, out_door) -> tuple[
    list, list, list, list, list, list, list]:
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
    contracts = open_cache_file_contracts('files/contracts_cache.pkl')
    try:
        excel_file = pd.ExcelFile(filename)
        sheet_names = excel_file.sheet_names
        inital_skip_rows = 9
        bad_names = []
        for sheet in sheet_names:
            data = get_data_from_cache_sheet('files/OCT_cache.csv', excel_file, sheet, inital_skip_rows)
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
                            contracts[sheet][name] = {}
                            contracts[sheet][name]["id"] = get_id_employee(name)
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
    with open('files/contracts_cache.pkl', 'wb') as file:
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
        cols = [0, 1, 2]
        # noinspection PyTypeChecker
        df = pd.read_excel(filename, skiprows=skip_rows, usecols=cols)
        df.dropna(inplace=True)
        df["Fecha/hora"] = clean_date(df["Fecha/hora"].tolist())
        df["Fecha/hora"] = pd.to_datetime(df["Fecha/hora"], format="mixed", dayfirst=True)
        df.dropna(subset=['Fecha/hora'], inplace=True)
        df["status"], df["name"], df["card"], df["in_out"] = clean_text(
            df["Texto"].to_list())
        df["in_out"] = clean_in_out(df["in_out"].tolist())
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
        if "OCTreport" not in k:
            continue
        pairs = []
        date1 = files_data[k]["date"]
        date1 = datetime.strptime(date1, '%d-%m-%Y')
        for k2 in files_data.keys():
            if "OCTreport" in k2:
                continue
            if k2 != k:
                date2 = files_data[k2]["date"]
                date2 = datetime.strptime(date2, '%d-%m-%Y')
                diff_dates = date1 - date2
                if 0 <= diff_dates.days <= 31 and date2 <= date1:
                    pairs.append(k2)
        files_data[k]["pairs"] = pairs if len(pairs) > 0 else None
    return files_data


def check_fichajes_files_in_directory(path: str, pattern1: str, pattern2: str) -> tuple[bool, dict]:
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
    :param pattern2: Pattern to detect in the name
    :param pattern1: Patter to detect in the name
    :param path: path to the directory
    :return: tuple with the boolean and the dictionary with the metadata of the files.
    """
    files = os.listdir(path)
    files_data = {}
    for file in files:
        if pattern1 in file or pattern2 in file:
            files_data[file] = get_metadata_file(path, file)
    if len(files_data) > 0:
        files_data = check_files_pairs_date(files_data)
    return False if len(files_data) == 0 else True, files_data


def get_dic_from_list_fichajes(lists_data: list) -> tuple:
    """
    Gets a dictionary from a list of data from fichajes files
    :param lists_data:
    :return:
    """
    dic_list = []
    for item in lists_data:
        if len(item) > 0:
            aux_dic = {}
            if len(item[0]) == 2:
                for timestamp, comment in item:
                    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    year = timestamp.year
                    month = timestamp.month
                    day = timestamp.day
                    if year not in aux_dic.keys():
                        aux_dic[year] = {}
                        aux_dic[year][month] = {}
                        aux_dic[year][month][day] = {}
                        aux_dic[year][month][day]["timestamp"] = str(timestamp)
                        aux_dic[year][month][day]["comment"] = comment
                        aux_dic[year][month][day]["value"] = None
                    else:
                        if month not in aux_dic[year].keys():
                            aux_dic[year][month] = {}
                            aux_dic[year][month][day] = {}
                            aux_dic[year][month][day]["timestamp"] = str(timestamp)
                            aux_dic[year][month][day]["comment"] = comment
                            aux_dic[year][month][day]["value"] = None
                        else:
                            if day not in aux_dic[year][month].keys():
                                aux_dic[year][month][day] = {}
                                aux_dic[year][month][day]["timestamp"] = str(timestamp)
                                aux_dic[year][month][day]["comment"] = comment
                                aux_dic[year][month][day]["value"] = None
                            else:
                                aux_dic[year][month][day]["timestamp"] = str(timestamp)
                                aux_dic[year][month][day]["comment"] = comment
                                aux_dic[year][month][day]["value"] = None
            else:
                for timestamp, comment, value in item:
                    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    year = timestamp.year
                    aux_dic[year] = {}
                    month = timestamp.month
                    aux_dic[year][month] = {}
                    day = timestamp.day
                    aux_dic[year][month][day] = {}
                    aux_dic[year][month][day]["timestamp"] = str(timestamp)
                    aux_dic[year][month][day]["comment"] = comment
                    aux_dic[year][month][day]["value"] = value
            dic_list.append(aux_dic)
        else:
            dic_list.append({})
    return tuple(dic_list)


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
                if value is not None:
                    total_value += value
    return total_days, total_value


def update_fichajes_resume_cache(filepath: str, data):
    """
    Updates the fichajes resume cache
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
    if update:
        for i, row in enumerate(fichajes_resume):
            (id_emp, name, contract, faltas, lates, extras, total_extra, primas,
             faltas_dic, lates_dic, extras_dic, primas_dic) = row
            for row2 in data:
                (id_emp2, name2, contract2, faltas2, lates2, extras2, total_extra2, primas2,
                 faltas_dic2, lates_dic2, extras_dic2, primas_dic2) = row2
                if id_emp == id_emp2:
                    faltas_dic.update(faltas_dic2)
                    lates_dic.update(lates_dic2)
                    extras_dic.update(extras_dic2)
                    primas_dic.update(primas_dic2)
                    break
            new_faltas, new_faltas_value = get_cumulative_data_fichajes_dict(faltas_dic)
            new_lates, new_lates_value = get_cumulative_data_fichajes_dict(lates_dic)
            new_extras, new_extras_value = get_cumulative_data_fichajes_dict(extras_dic)
            new_primas, new_primas_value = get_cumulative_data_fichajes_dict(primas_dic)
            aux = (id_emp, name, contract, new_faltas, new_lates, new_extras, new_extras_value, new_primas,
                   faltas_dic, lates_dic, extras_dic, primas_dic)
            fichajes_resume[i] = aux
    print(fichajes_resume)
    with open(filepath, 'wb') as file:
        pickle.dump(fichajes_resume, file)


def get_fichajes_resume_cache(filepath) -> tuple[list, bool]:
    """
    Gets the fichajes resume cache if exists else the data is obtained from the
    db, and then the cumulative values of absences, delays, extra hours and primes
    are calculated.
    :param filepath:
    :return:
    """
    try:
        with open(filepath, 'rb') as file:
            fichajes_resume = pickle.load(file)
        flag = False if len(fichajes_resume) == 0 else True
    except Exception as e:
        print("Error at getting cache file: ", e)
        fichajes_resume = []
        flag = False
    if not flag:
        flag, error, result = get_all_fichajes()
        if flag and len(result) > 0:
            fichajes_resume = []
            for row in result:
                (name, lastname, id_fich, id_emp, contract, absences, lates, extras, primes) = row
                new_faltas, new_faltas_value = get_cumulative_data_fichajes_dict(json.loads(absences))
                new_tardanzas, new_tardanzas_value = get_cumulative_data_fichajes_dict(json.loads(lates))
                new_extras, new_extras_value = get_cumulative_data_fichajes_dict(json.loads(extras))
                new_primas, new_primas_value = get_cumulative_data_fichajes_dict(json.loads(primes))
                new_row = (id_emp, name.title() + lastname.title(), contract, new_faltas, new_tardanzas,
                           new_extras, new_extras_value, new_primas, json.loads(absences),
                           json.loads(lates), json.loads(extras), json.loads(primes))
                fichajes_resume.append(new_row)
            update_fichajes_resume_cache(filepath, fichajes_resume)
        else:
            fichajes_resume = []
            print("Error at getting fichajes from sql: ", error)
            flag = False
    return fichajes_resume, flag


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
