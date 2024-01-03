# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:37 $'

import csv
import os
import pickle
import re
import time
from tkinter import Misc, Frame, messagebox
from tkinter.ttk import Treeview

import dropbox
import mysql.connector
import pandas as pd
import ttkbootstrap as ttk

from static.extensions import secrets
from templates.FunctionsSQL import get_id_employee
from templates.FunctionsText import clean_accents


def check_only_read_conflict(name: str):
    """
    Check if the file is read only
    :param name: name of the file
    :return: True if the file is read only, False otherwise
    """
    ignore_patterns = [".*conflictos de solo lectura.*", ".*cache.*", ".*desktop.ini"]
    pattern = "|".join(ignore_patterns)
    if re.match(pattern, name):
        return True
    return False


def get_files_foldes_dropbox(fname: str, online=False):
    """
    Gets the files and folders from dropbox
    :param online:
    :param fname: name of the folder
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
    :param fname: name of the folder
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
    :param online: read in online dropbox or local files
    :param rpaths: directory to save
    :param exclude: list of folders to exclude
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


def load_directory_file(paths: dict, exclude: list = None, local=False):
    """
    Loads the directory from a file
    :param local:
    :param exclude: list of folders to exclude
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
    :param paths: directory to save
    :param dir_list: directory to save
    :return:
    """
    local_name = "_local" if local else ""
    for index, item in enumerate(paths):
        local_file = 'files/folders_' + item + local_name + '.pkl'
        with open(local_file, 'wb') as f:
            pickle.dump(dir_list[index], f)


def clean_date(dates: list):
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


def clean_in_out(in_out: list):
    for i, str_in_out in enumerate(in_out):
        if str_in_out is not None:
            if "OUT" in str_in_out:
                in_out[i] = "FUERA"
            if "IN" in str_in_out:
                in_out[i] = "IN"
        else:
            in_out[i] = ""
    return in_out


def clean_text(texts: list):
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


def validate_digits_numbers(new_value):
    # Returning True allows the edit to happen, False prevents it.
    return new_value.isdigit()


def create_spinboxes_time(master: Misc, father, row: int, column: int,
                          pad_x: int = 5, pad_y: int = 5,
                          style: str = 'primary', title: str = "",
                          mins_defaul=0, hours_default=8) -> Frame | None:
    """ Creates a clock with two spinboxes for minutes and hours
    :param title:
    :param father:
    :param master: <Misc> master where the object is created
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


def make_empy_zeros(txt: str):
    """
    Makes the string txt empty if it is empty or contains only zeros
    :param txt:
    :return:
    """
    return 0 if txt == "" or None else float(txt)


def clean_data_contract(status, fechas, comments, extras, primas, in_door, out_door):
    for i, item in enumerate(extras):
        extras[i] = make_empy_zeros(item)
    for i, item in enumerate(primas):
        primas[i] = "NO" if item == "" or None else "SI"
    return status, fechas, comments, extras, primas, in_door, out_door


def clean_parenthesis_txt(name: str):
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


def extract_data_file_contracts(filename: str) -> dict:
    """
    Extracts the data from a file from operations and from cache on a directory.
    :param filename:
    :return: {contracts_name: {employee_name:  {status: [], fechas: [], comments: [], extras: [], primas: [], in_door: [], out_door: []}}}
    """
    try:
        with open('files/contracts_cache.pkl', 'rb') as f:
            contracts = pickle.load(f)
    except Exception as e:
        print(e)
        contracts = {}
    try:
        excel_file = pd.ExcelFile(filename)
        sheet_names = excel_file.sheet_names
        inital_skip_rows = 9
        for sheet in sheet_names:
            if sheet == "VEHICULOS":
                continue
            skip_rows = [i for i in range(0, inital_skip_rows)]
            # skip_rows = [i for i in range(9)] + [i for i in range(13, 3142)]
            df = pd.read_excel(excel_file, skiprows=skip_rows, sheet_name=sheet)
            df.to_csv('files/OCT_report_1.csv')
            data = []
            with open('files/OCT_report_1.csv', mode="r",
                      encoding='utf-8') as csv_file:  # "r" represents the read mode
                reader = csv.reader(csv_file)  # this is the reader object
                for item in reader:
                    data.append(item)
            contracts[sheet] = {} if sheet not in contracts.keys() else contracts[sheet]
            name = ""
            emp_id = 0
            indexes = range(len(data))
            starting_indexes = [indexes[i] for i in range(0, len(indexes), 4)]
            data_sliced = [data[i:i + 4] for i in starting_indexes]
            for data_aux in data_sliced:
                status = []
                fechas = []
                comments = []
                extras = []
                primas = []
                in_door = []
                out_door = []
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
                if name != "":
                    status, fechas, comments, extras, primas, in_door, out_door = clean_data_contract(
                        status, fechas, comments, extras, primas, in_door, out_door)
                    if name not in contracts[sheet].keys():
                        contracts[sheet][name] = {}
                        contracts[sheet][name]["id"] = get_id_employee(name)
                    contracts[sheet][name]["fechas"] = fechas
                    contracts[sheet][name]["status"] = status
                    contracts[sheet][name]["comments"] = comments
                    contracts[sheet][name]["extras"] = extras
                    contracts[sheet][name]["primas"] = primas
                    contracts[sheet][name]["in_door"] = in_door
                    contracts[sheet][name]["out_door"] = out_door

    except Exception as e:
        print(e)
        messagebox.showerror("Error",
                             "Error al leer el archivo.\n"
                             " Asegurese sea el archivo correcto, con el formato correcto.\n" + str(e)
                             )
    with open('files/contracts_cache.pkl', 'wb') as file:
        pickle.dump(contracts, file)
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
    :param path: parent path of the file
    :param file: name of the file
    :return: dictionary of the file. {path, extension, size, report, date}

    """
    out = {
        "path": path + file,
        "extension": file.split(".")[-1],
        "size": os.path.getsize(os.path.join(path, file)),
        "report": "",
        "date": "",
    }
    file = remove_extensions([file])[0]
    names = file.split("_")
    if len(names) > 1:
        out["report"] = names[0]
        out["date"] = names[1]
    return out


def check_fichajes_files_in_directory(path: str, pattern1: str, pattern2: str):
    """
    Checks if the files in the directory are fichajes files
    :param pattern2: pattern to detect in the name
    :param pattern1: patter to detect in the name
    :param path: path to the directory
    :return:
    """
    files = os.listdir(path)
    files_data = {}
    for file in files:
        if pattern1 in file or pattern2 in file:
            files_data[file] = get_metadata_file(path, file)
    return False if len(files_data) == 0 else True, files_data
