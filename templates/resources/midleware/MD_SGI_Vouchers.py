# -*- coding: utf-8 -*-
"""Anexos de los vales EPP y de herramientas. La receta (lookup por id sin ventana
de fecha, nombre "<id>-<archivo>", S3 + escritura condicional de `files` con
reintentos) vive en Functions_Aux_Vouchers y es la misma del checklist
vehicular (docs/checklist_vehicular_anexos_sin_carrera.md, P-103)."""

from templates.resources.methods.Functions_Aux_Vouchers import attach_voucher_file

__author__ = "Edisson Naula"
__date__ = "$ 06/jun/2025  at 14:54 $"


def create_voucher_epp_attachment_api(data, data_token):
    """{"filepath": filepath_download, "filename": filename, "id_voucher": id}, data_token"""
    return attach_voucher_file("epp", data, data_token)


def create_voucher_tools_attachment_api(data, data_token):
    """{"filepath": filepath_download, "filename": filename, "id_voucher": id}, data_token"""
    return attach_voucher_file("tools", data, data_token)
