# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 07/sep./2026  at 12:00 $"

from flask_restx import fields
from wtforms import IntegerField, StringField
from wtforms.form import Form
from wtforms.validators import InputRequired, Optional

from static.constants import api

# =====================================================================
# Almacén multisede — lado principal (rs_Almacen.py): catálogo de sedes e
# inventario consolidado (F1); traslados (F3). Doble capa: api.model
# (swagger) + WTForms (validación runtime). `extra_info` es JSON libre: el
# form NO lo valida, el midleware lo toma del ns.payload crudo.
# Ver docs/almacen_multisede_f1.md.
# =====================================================================

warehouse_post_model = api.model(
    "WarehousePost",
    {
        "name": fields.String(required=True, description="Nombre de la sede (único)", example="Sucursal Monterrey"),
        "extra_info": fields.Raw(
            required=False,
            description="Datos libres de la sede: {address, manager, phone, ...}",
            example={"address": "Av. X 123", "manager": "Juan Pérez"},
        ),
    },
)

warehouse_put_model = api.model(
    "WarehousePut",
    {
        "id_warehouse": fields.Integer(required=True, description="Id de la sede", example=2),
        "name": fields.String(required=False, description="Nuevo nombre (único)"),
        "is_active": fields.Integer(required=False, description="0 = baja suave, 1 = reactivar (la principal no se da de baja)"),
        "extra_info": fields.Raw(
            required=False,
            description="Merge por llave sobre el extra_info actual; null en una llave la quita",
        ),
    },
)


class WarehousePostForm(Form):
    name = StringField("name", validators=[InputRequired()])


class WarehousePutForm(Form):
    id_warehouse = IntegerField("id_warehouse", validators=[InputRequired()])
    name = StringField("name", validators=[Optional()], default=None)
    # is_active y extra_info se leen del payload crudo (parcial: solo llaves presentes)
