# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/nov./2023  at 16:55 $'

import unicodedata


def clean_accents(txt: str):
    return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


def compare_employee_name(names_1, id_2):
    for id_1, name in names_1:
        if id_1 is not None:
            if id_1 == id_2:
                return name, id_1, True
    return None, None, False


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
            case 4:
                out = {
                    "username": data['username'],
                    "password": data['password'],
                    "permissions": data['permissions']
                }
            case 5:
                out = {
                    "limit": data['limit'],
                    "page": data['page']
                }
            case 6 | 8:
                id_sm = data['info']['id'] if mode == 8 else None
                info = {
                        'id': id_sm,
                        "sm_code": data['info']['sm_code'],
                        "folio": data['info']['folio'],
                        "contract": data['info']['contract'],
                        "facility": data['info']['facility'],
                        "location": data['info']['location'],
                        "client_id": data['info']['client_id'],
                        "emp_id": data['info']['emp_id'],
                        "date": data['info']['date'],
                        "limit_date": data['info']['limit_date'],
                        "status": data['info']['status'],
                        "order_quotation": data['info']['order_quotation'],
                        "comment": data['info']['comment'],
                        "history": data['info']['history']
                    }
                items = []
                for item in data['items']:
                    items.append({
                        'id': item['id'],
                        "quantity": item['quantity'],
                        "comment":  item['comment']
                    })
                out = {
                    "info": info,
                    "items": items,
                    "id_sm": id_sm
                }
            case 7:
                out = {
                    "id": data['id'],
                    "sm_code": data['sm_code'],
                }
            case 9:
                out = {
                    'date': data['date'],
                }
            case 10 | 11:
                value = data['value'] if mode == 10 else None
                comment = data['comment'] if mode == 10 else None
                out = {
                        'id': data['id'],
                        "date": data['date'],
                        "event": data['event'],
                        "value": value,
                        "comment": comment,
                        "contract": data['contract'],
                        "id_emp": data['id_emp']
                    }
            case 12:
                out = {
                    'name': data["name"],
                    'address': data["address"],
                    'phone': data["phone"],
                    'email': data["email"],
                    'rfc': data["rfc"]
                }
            case 13:
                out = {
                    'name': data["name"],
                    'stock': data["stock"],
                    'udm': data["udm"],
                    'supplier': data["supplier"],
                    'category': data["category"],
                    'sku':  data["sku"]
                }
            case 14:
                out = {"id": data["id"] if "id" in data.keys() else None, "info": {
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
