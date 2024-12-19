# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/jun./2024  at 17:07 $"

from static.constants import cache_file_nominas

import json


def write_file_cache_nominas(data: dict):
    """
    writes a JSON file with the data of the payrolls
    :param data:
    :return:
    """
    json.dump(data, open(cache_file_nominas, "w"))
    return 200, "OK"
