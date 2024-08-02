# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 28/jun./2024  at 17:07 $'

from static.extensions import cache_file_nominas
from templates.Functions_Text import validate_seniority_dict

import json


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
                    "id": data["id"] if "id" in data.keys() else None,
                    "info": {
                        "name": data["info"]["name"],
                        "lastname": data["info"]["lastname"],
                        "phone": data["info"]["phone"],
                        "dep": data["info"]["dep"],
                        "modality": data["info"]["modality"],
                        "email": data["info"]["email"],
                        "contract": data["info"]["contract"],
                        "admission": data["info"]["admission"],
                        "rfc": data["info"]["rfc"],
                        "curp": data["info"]["curp"],
                        "nss": data["info"]["nss"],
                        "emergency": data["info"]["emergency"],
                        "position": data["info"]["position"],
                        "status": data["info"]["status"],
                        "departure": data["info"]["departure"],
                        "birthday": data["info"]["birthday"],
                        "legajo": data["info"]["legajo"]
                    } if "info" in data.keys() else {}}

            case 2:
                out = {"id": data["id"] if "id" in data.keys() else None, "info": {
                    "name": data["info"]["name"],
                    "blood": data["info"]["blood"],
                    "status": data["info"]["status"],
                    "aptitudes": data["info"]["aptitudes"],
                    "dates": data["info"]["dates"],
                    "apt_actual": data["info"]["apt_actual"],
                    "emp_id": data["info"]["emp_id"]
                } if "info" in data.keys() else {}}
            case 3:
                out = {
                    "emp_id": data["emp_id"],
                    "seniority": data["seniority"] if validate_seniority_dict(data) and "seniority" in data.keys() else None
                }
            case 4:
                out = {
                    "files": data["files"] if "files" in data.keys() else None,
                    "grace_init": data["grace_init"] if "grace_init" in data.keys() else 10,
                    "grace_end": data["grace_end"] if "grace_end" in data.keys() else 10,
                    "time_in":  data["time_in"] if "time_in" in data.keys() else "08:00",
                    "time_out": data["time_out"] if "time_out" in data.keys() else "18:00"
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


def write_file_cache_nominas(data: dict):
    """
    writes a JSON file with the data of the payrolls    
    :param data: 
    :return: 
    """
    json.dump(data, open(cache_file_nominas, "w"))
    return 200, "OK"
