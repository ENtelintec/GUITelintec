# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/ene./2024  at 15:31 $'

from typing import Any

import ttkbootstrap as ttk
from tkinter import StringVar

from static.extensions import ventanasApp


def create_label(master, row, column, padx=5, pady=5, text=None, textvariable=None,
                 font=('Helvetica', 10, 'normal'), columnspan=1, sticky=None):
    """
    Create a label with the text-provided
    :param sticky:
    :param columnspan:
    :param text: If None, a label with textvariable is created
    :param font:
    :param master: Parent of the label
    :param textvariable: textvariable of the label
    :param row: row to place the widget
    :param column: Column to place the widget
    :param padx:
    :param pady:
    :return: Placed label in the grid
    """
    if text is not None:
        label = ttk.Label(master, text=text, font=font)
    else:
        label = ttk.Label(master, textvariable=textvariable, font=font)
    if sticky is None:
        label.grid(row=row, column=column, padx=padx, pady=pady, columnspan=columnspan)
    else:
        label.grid(row=row, column=column, padx=padx, pady=pady, columnspan=columnspan, sticky=sticky)
    return label


def create_Combobox(master, values, width=None, row=0, column=0,
                    state="readonly", padx=5, pady=5, columnspan=1, *args, **kwargs):
    """
    Create a combobox with the values provided
    :param columnspan:
    :param master: parent of the combobox
    :param values: values of the combobox
    :param row: row to place the widget
    :param column: Column to place the widget
    :param state: state of the combobox
    :param padx:
    :param pady:
    :param width:
    :return: Placed combobox in the grid
    """
    combobox = ttk.Combobox(master, values=values, state=state)
    if len(values) > 0:
        combobox.current(0)
    for k, v in kwargs.items():
        if k == "sticky":
            combobox.grid(row=row, column=column, padx=padx, pady=pady, columnspan=columnspan, sticky=v)
    combobox.grid(row=row, column=column, padx=padx, pady=pady, columnspan=columnspan)
    return combobox


def compare_permissions_windows(user_permissions: list) -> tuple[bool, Any] | tuple[bool, None]:
    """
    This method is used to compare the permissions of a user.
    :param user_permissions: list of permissions of the user
    :return: bool with the result of the comparison
    """
    for permission in user_permissions:
        if permission in ventanasApp.keys():
            return True, ventanasApp[permission]
    return False, None


def create_button_side_menu(master, row, column, text, image=None, command=None, columnspan=1):
    """
    This method is used to create a button in the side menu.
    :param columnspan:
    :param image: image for the button
    :param command: command for the button
    :param master: father for the button
    :param row: row for the button
    :param column: column for the button
    :param text: text for the button
    """
    button = ttk.Button(master,
                        text=text,
                        image=image, compound="left", command=command)
    button.grid(row=row, column=column, sticky="nsew", pady=5, padx=5, columnspan=columnspan)
    button.image = image
    # button.configure(text=text, command=command)
    return button


def update_stringvars(stringvar_list: list[tuple[StringVar, str]]):
    """
    Update the stringvar list with the new value
    :param stringvar_list: list of stringvars
    :return: None
    """
    for stringvar, value in stringvar_list:
        stringvar.set(value)


def create_stringvar(number: int, value: str):
    """
    Create a stringvar with the number provided initialized with ""
    :param value: Starting value of the stringvar
    :param number: number to create the stringvar
    :return: tuple
    """
    return [ttk.StringVar(value=value) for _ in range(number)]


def create_var_none(number: int):
    """
    Create a tuple with the number provided
    :param number: number of values to create
    :return: tuple
    """
    var_none = []
    for i in range(number):
        var_none.append(None)
    return tuple(var_none)
