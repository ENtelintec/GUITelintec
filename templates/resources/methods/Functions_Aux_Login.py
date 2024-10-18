# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/sept/2024  at 14:21 $"

import jwt

from static.extensions import secrets


def unpack_token(token: str) -> dict:
    """
    Unpacks the token.
    :param token: <string>
    :return: <dict>
    """
    return jwt.decode(token, secrets.get("TOKEN_MASTER_KEY"), algorithms="HS256")


def verify_department_permission(token_data: dict, department: str) -> bool:
    """
    Verifies the department permission.
    :param token_data: <dict>
    :param department: <string>
    :return: <bool>
    """
    try:
        permissions = token_data.get("permissions", {})
        print("permissions: ", permissions)
        for item in permissions.values():
            if department.lower() in item.lower():
                return True
        return False
    except Exception as e:
        print("errort at verifyin permission for department: ", e)
        return False


def verify_employee_id(token_data: dict, emp_id: int) -> bool:
    """
    Verifies the employee id.
    :param token_data: <dict>
    :param emp_id: <integer>
    :return: <bool>
    """
    try:
        id_emp = token_data.get("emp_id", None)
        if id_emp == emp_id:
            return True
    except Exception as e:
        print("errort at verifyin employee id: ", e)
        return False


def verify_token(
    token: str, department: str = None, emp_id: int = None
) -> tuple[bool, dict]:
    """
    Verifies the token.
    :param emp_id: <integer>
    :param token: <string>
    :param department: <string>
    :return: <bool>
    """
    try:
        data = unpack_token(token)
        if emp_id:
            if not verify_employee_id(data, emp_id):
                return False, {}
        elif department:
            if not verify_department_permission(data, department):
                return False, {}
        return True, data
    except Exception as e:
        print("errort at unpack token: ", e)
        return False, {}
