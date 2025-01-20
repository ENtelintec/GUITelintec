# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/sept/2024  at 14:21 $"

import jwt

from static.constants import secrets


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
        for item in permissions.values():
            if department.lower() in item.lower():
                return True
        return False
    except Exception as e:
        print("errort at verifyin permission for department: ", e)
        return False


def verify_department_or_employee_permission(
    token_data: dict, department: str, emp_id: int
) -> bool:
    """
    Verifies the department or employee permission.
    :param token_data: <dict>
    :param department: <string>
    :param emp_id: <integer>
    :return: <bool>
    """
    try:
        permissions = token_data.get("permissions", {})
        if verify_employee_id(token_data, emp_id):
            return True
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


def token_verification_procedure(request, **kwargs):
    """
    Verifies the token.
    :param request: <request>
    :return: <bool>, <data>
    """
    try:
        token = request.headers.get("Authorization", None)
        if token is None:
            return False, {}, "Token not found"
        department = kwargs.get("department", None)
        emp_id = kwargs.get("emp_id", None)
        flag, data_token = verify_token(token, department, emp_id)
        return flag, data_token, ""
    except Exception as e:
        msg = "errort at token verification procedure: " + str(e)
        return False, {}, msg


def verify_token(
    token: str, department: str | list = None, emp_id: int = None
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
            if verify_employee_id(data, emp_id):
                return True, data
        if department:
            if isinstance(department, list):
                for dep in department:
                    if verify_department_permission(data, dep):
                        return True, data
            elif isinstance(department, str):
                if verify_department_permission(data, department):
                    return True, data
        return False, {}
    except Exception as e:
        print("errort at unpack token: ", e)
        return False, {}
