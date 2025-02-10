# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/jun./2024  at 16:33 $"

from datetime import datetime


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
        date1 = datetime.strptime(date1, "%d-%m-%Y")
        for k2 in files_data.keys():
            if "Fichaje" in k2:
                continue
            if k2 != k:
                date2 = files_data[k2]["date"]
                date2 = datetime.strptime(date2, "%d-%m-%Y")
                diff_dates = date1 - date2
                if 0 <= diff_dates.days <= 31 and date2 <= date1:
                    pairs.append(k2)
        files_data[k]["pairs"] = pairs if len(pairs) > 0 else None
    return files_data


def remove_extensions(files: list):
    """
    Removes the extensions from the files
    :param files:
    :return:
    """
    for i, file in enumerate(files):
        files[i] = file.split(".")[0]
    return files


def get_metadata_file_fichaje(file: str, filename):
    """
    Gets the metadata from the file (empresa)_(date).ext.
    The dictionary contains the path, extension, size, report, date.
    The report and date are empty if the file is not a fichaje file.
    The date is in the format yyyy-mm-dd.
    The report is the first word before the date.
    The date is the second word before the date.
    The report and date are empty if the file is not a fichaje file.
    :param file: url of the file
    :return: dictionary of the file.
    {Path, extension, size, report, date}

    """
    out = {
        "path": file,
        "extension": file.split(".")[-1],
        "report": "",
        "date": "",
        "pairs": None,
        "name": filename,
    }
    filename = remove_extensions([filename])[0]
    names = filename.split("_")
    if len(names) > 1:
        out["report"] = names[0]
        out["date"] = names[1]
    return out


def check_fichajes_files_in_directory(patterns: list) -> tuple[bool, dict]:
    """
    Checks if the files in the directory are fichajes files
    The dictionary contains the path, extension, size, report, date.
    The report and date are empty if the file is not a fichaje file.
    The date is in the format yyyy-mm-dd.
    The report is the first word before the date.
    The date is the second word before the date.
    The report and date are empty if the file is not a fichaje file.
    The dictionary is empty if the files aren't fichajes files.
    The boolean is False if the files aren't fichajes files.
    :param patterns: Patterns to detect in the name
    :return: tuple with the boolean and the dictionary with the metadata of the files.
    """
    from templates.resources.midleware.Functions_midleware_RRHH import (
        get_files_fichaje_shrpt,
    )

    code, files = get_files_fichaje_shrpt()
    # files = os.listdir(path)
    files_data = {}
    for file in files:
        # check in file contains any pattern in the patterns list
        for pattern in patterns:
            if pattern in file:
                filename = file.split("/")[-1]
                files_data[filename] = get_metadata_file_fichaje(file, filename)
    if len(files_data) > 0:
        files_data = check_files_pairs_date(files_data)
    return False if len(files_data) == 0 else True, files_data
