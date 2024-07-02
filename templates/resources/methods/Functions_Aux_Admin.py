# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 20/jun./2024  at 15:40 $'

from static.extensions import path_contract_files


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
                    "id": data['id'] if "id" in data.keys() else None,
                    "metadata":  data['metadata'] if "metadata" in data.keys() else None,
                    "products": data['products'] if "products" in data.keys() else None,
                    "creation": data['creation'] if "creation" in data.keys() else None,
                    "timestamps": data['timestamps'] if "timestamps" in data.keys() else None,
                }
            case 2:
                out = {
                    "id": data['id'] if "id" in data.keys() else None,
                    "metadata": data['metadata'] if "metadata" in data.keys() else None,
                    "products": data['products'] if "products" in data.keys() else None,
                    "creation": data['creation'] if "creation" in data.keys() else None,
                    "timestamps": data['timestamps'] if "timestamps" in data.keys() else None,
                    "quotation_id": data['quotation_id'] if "quotation_id" in data.keys() else None,
                }
            case _:
                print("Invalid mode")
                code = 204
                out = {
                    "error": "Invalid mode"
                }
    except Exception as e:
        print(e)
        code = 400
        out = {
            "error": "Invalid sintaxis" + str(e)
        }
    return code, out


def get_filenames_contracts(path=path_contract_files):
    """
    Gets the filenames of the contracts.
    :return: <list>
    """
    import os
    filenames = os.listdir(path)
    # check if the filenames are valid
    for filename in filenames:
        if not filename.endswith(".pdf"):
            filenames.remove(filename)
    return filenames
