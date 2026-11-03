# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/nov./2023  at 17:37 $"

import json
import os
import pickle
import warnings
from datetime import datetime

import pandas as pd
import pytz

from static.constants import (
    format_date,
    timezone_software,
)
from templates.controllers.fichajes.fichajes_controller import (
    get_all_fichajes,
    insert_new_fichaje_DB,
    update_fichaje_DB,
)


def load_directory_file(paths: dict, exclude: list | None = None, local=False) -> list:
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
        return self.name + " " + str(self.father) + " " + str(len(self.children)) + " " + str(len(self.files))

    def __repr__(self):
        return self.name


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
                    if date.month <= int(month) and date.year <= int(year) and date.day <= int(day):
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


def update_fichajes_resume_cache(filepath: str, data: list, just_file=False):
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
    if not (isinstance(fichajes_resume, list)):
        return False, "Badn data db"
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
                        new_total.append(get_cumulative_data_fichajes_dict(dicts_old[i])[0])
                        new_value.append(get_cumulative_data_fichajes_dict(dicts_old[i])[1])
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
            flag = False if len(fichajes_resume) == 0 or fichajes_resume is None else True
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
                new_faltas, new_faltas_value = get_cumulative_data_fichajes_dict(json.loads(absences))
                new_tardanzas, new_tardanzas_value = get_cumulative_data_fichajes_dict(json.loads(lates))
                new_extras, new_extras_value = get_cumulative_data_fichajes_dict(json.loads(extras))
                new_primas, new_primas_value = get_cumulative_data_fichajes_dict(json.loads(primes))
                new_early, new_early_value = get_cumulative_data_fichajes_dict(json.loads(early))
                new_pasiva, new_pasiva_value = get_cumulative_data_fichajes_dict(json.loads(pasiva))
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


def write_log_file(paths: list | str, text, data_token=None):
    if data_token and data_token["is_tester"]:
        return True
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


