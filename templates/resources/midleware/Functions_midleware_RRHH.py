# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 28/jun./2024  at 16:28 $'

from static.extensions import files_fichaje_path, patterns_files_fichaje
from templates.misc.Functions_Files_RH import check_fichajes_files_in_directory


def get_files_fichaje():
    flag, files = check_fichajes_files_in_directory(files_fichaje_path, patterns_files_fichaje)
    if not flag:
        return False, files
    files_list = [v for k, v in files.items()]
    return True, files_list

