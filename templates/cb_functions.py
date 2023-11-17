# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 02/nov./2023  at 17:37 $'

import json
import os
import pickle
import re
import time
from tkinter import Misc, Frame
from tkinter.ttk import Treeview
from typing import List, Union
import ttkbootstrap as ttk
import dropbox
import jwt
import mysql.connector

from static.extensions import secrets


def execute_sql(sql: str, values: tuple = None, type_sql=1):
    """
    Execute the sql with the values provides (or not) and returns a value
    depending on the type of query. In case of exception returns None
    :param type_sql: type of query to execute
    :param sql: sql query
    :param values: values for sql query
    :return:
    """
    mydb = mysql.connector.connect(
        host=secrets["HOST_DB"],
        user=secrets["USER_SQL"],
        password=secrets["PASS_SQL"],
        database="sql_telintec"
    )
    my_cursor = mydb.cursor()
    out = []
    e = None
    try:
        match type_sql:
            case 2:
                my_cursor.execute(sql, values)
                out = my_cursor.fetchall()
            case 1:
                my_cursor.execute(sql, values)
                out = my_cursor.fetchone()
            case 3:
                my_cursor.execute(sql, values)
                mydb.commit()
                out = my_cursor.rowcount
            case 4:
                my_cursor.execute(sql, values)
                mydb.commit()
                out = my_cursor.lastrowid
            case 5:
                my_cursor.execute(sql)
                out = my_cursor.fetchall()
            case _:
                out = []
    except Exception as e:
        print(e)
        out = []
        return out, e
    finally:
        out = out if out is not None else []
        my_cursor.close()
        mydb.close()
        return out, e


def verify_user_DB(user: str, password: str) -> bool:
    """
    Verifies if the user and password are correct.
    :param password: <string>
    :param user: <string>
    :return: <boolean>
    """
    sql = "SELECT usernames FROM users_system " \
          "WHERE usernames = %s AND password = %s"
    val = (user, password)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchone()
    result, e = execute_sql(sql, val)
    flag = True if len(result) > 0 else False
    return flag


def generate_token(user: str, user_key: str, password: str) -> List[Union[None, int]]:
    """
    Generates a token for the user.
    :param user_key: <string>
    :param password: <string>
    :param user: <string>
    :return: <string>
    """
    sql = "SELECT permissions FROM users_system WHERE usernames = %s AND password = %s"
    val = (user, password)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchone()
    result, e = execute_sql(sql, val)
    if result is not None:
        permissions = json.loads(result[0])
        data = {"name": user_key,
                "pass": password,
                "permissions": permissions}
        return [jwt.encode(data, secrets.get("TOKEN_MASTER_KEY"), algorithm="HS256"), 201]
    else:
        return [None, 404]


def update_DB_token(user: str, token: str, expires_in: int) -> int:
    """
    Updates the token for the user.
    :param expires_in: int
    :param user: <string>
    :param token: <string>
    :return: None
    """
    sql = "SELECT usernames FROM users_system " \
          "WHERE usernames = %s"
    val = (user,)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchone()
    result, e = execute_sql(sql, val)
    code = 200
    if result is not None:
        sql = "UPDATE users_system " \
              "SET token = %s, exp = %s , timestamp_token = %s " \
              "WHERE usernames = %s"
        timestamp_token = time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime())
        val = (token, expires_in, timestamp_token, user)
        # my_cursor.execute(sql, val)
        # mydb.commit()
        execute_sql(sql, val, 3)
    else:
        print("User not found")
        code = 204

    return code


def get_token_info(user: str) -> List[Union[str, int, str, int]]:
    """
    Gets the token information for the user.
    :param user: <string>
    :return: <list> [<token>, <expires_in>, <timestamp_token>, <code>
        <token>: <string>
        <expires_in>: <int>
        <timestamp_token>: <string>
        <code>: <int>
    """
    sql = "SELECT token, exp, timestamp_token FROM users_system " \
          "WHERE usernames = %s AND token IS NOT NULL"
    val = (user,)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchone()
    result, e = execute_sql(sql, val)
    code = 200
    if len(result) > 0:
        token = result[0]
        expires_in = result[1]
        timestamp_token = result[2]
    else:
        print("User not found")
        token = None
        expires_in = None
        timestamp_token = None
        code = 204

    return [token, expires_in, timestamp_token, code]


def verify_token(token: str, user: str) -> bool:
    """
    Verifies if the token is valid.
    :param user: <string>
    :param token: <string>
    :return: <boolean>
    """
    sql = "SELECT token FROM users_system " \
          "WHERE usernames = %s"
    val = (user,)
    # my_cursor.execute(sql, val)
    # result = my_cursor.fetchall()
    result, e = execute_sql(sql, val, 2)
    flag = False
    if result is not None:
        for i in result:
            if i[0] == token:
                flag = True
    return flag


def unpack_token(token: str) -> dict:
    """
    Unpacks the token.
    :param token: <string>
    :return: <dict>
    """
    return jwt.decode(token, secrets.get("TOKEN_MASTER_KEY"), algorithms="HS256")


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
                    "username": data['username'],
                    "password": data['password']
                }
            case 2:
                out = {
                    "username": data['username']
                }
            case 3:
                out = {
                    "token": data['token']
                }
            case _:
                print("Invalid mode")
                code = 204
                out = {
                    "error": "Invalid mode"
                }
    except Exception as e:
        print(e)
        code = 404
        out = {
            "error": "Invalid sintaxis" + str(e)
        }

    return code, out


def delete_token_DB(user: str):
    """
    Deletes the token for the user.
    :param user: <string>
    :return: None
    """
    sql = "UPDATE users_system " \
          "SET token = NULL, exp = NULL, timestamp_token = NULL " \
          "WHERE usernames = %s"
    val = (user,)
    result, e = execute_sql(sql, val, 3)
    flag = True if e is None else False
    return flag, e


def verify_user_DB_token(user: str, token: str):
    """
    Verifies if the user and token are correct.
    :param user: <string>
    :param token: <string>
    :return: <boolean>
    """
    sql = "SELECT usernames FROM users_system " \
          "WHERE usernames = %s AND token = %s"
    val = (user, token)
    result, e = execute_sql(sql, val)
    flag = True if len(result) > 0 else False
    return flag


def get_permissions(token: str):
    """
    Gets the permissions for the user.
    :param token: <string>
    :return: <list> [<permissions>, <code>
        <permissions>: <list>
        <code>: <int>
    """
    sql = "SELECT usernames, permissions FROM users_system " \
          "WHERE token = %s"
    val = (token,)
    result, e = execute_sql(sql, val, 2)
    if len(result) > 0:
        username = result[0][0]
        permissions = json.loads(result[0][1])
    else:
        print("User not found")
        permissions = None
        username = None
    return permissions, username


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
    minutes_spinbox = ttk.Spinbox(clock, from_=0, to=59, bootstyle=style,
                                  width=2, justify="center")
    minutes_spinbox.grid(row=0, column=1, padx=1, pady=1, sticky="w")
    # hours spinbox
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
