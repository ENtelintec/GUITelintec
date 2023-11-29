# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 29/nov./2023  at 16:55 $'
import unicodedata


def clean_accents(txt: str):
    return unicodedata.normalize('NFKD',txt).encode('ASCII', 'ignore').decode('ASCII')
