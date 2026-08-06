# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026  at 12:00 $"

from flask_restx import fields
from wtforms import IntegerField, StringField
from wtforms.form import Form
from wtforms.validators import InputRequired

from static.constants import api

# =====================================================================
# Modelos de encuesta (template + rubrica) — /GUI/api/v1/rrhh/quizz/models
# Doble capa: api.model (swagger/docs) + WTForms Form (validacion runtime).
# `template` y `rubric` son JSON arbitrario: el form NO los valida (WTForms
# no modela dicts); el midleware los toma del ns.payload crudo y los valida
# estructuralmente (_validate_template / validate_rubric + dry-run).
# Ver Docs/quizz_models_crud.md.
# =====================================================================

quizz_model_post_model = api.model(
    "QuizzModelPost",
    {
        "name": fields.String(
            required=True,
            description="Nombre visible del modelo",
            example="Encuesta de seguridad 2026",
        ),
        "template": fields.Raw(
            required=True,
            description='Cuestionario: {"<n>": {question, subquestions, options, answer, type}}',
        ),
        "rubric": fields.Raw(
            required=False,
            description="Rúbrica del motor (opcional; se puede agregar después con PUT)",
        ),
    },
)

quizz_model_put_model = api.model(
    "QuizzModelPut",
    {
        "name": fields.String(required=False, description="Nuevo nombre"),
        "template": fields.Raw(
            required=False, description="Solo editable en BORRADOR (status 0)"
        ),
        "rubric": fields.Raw(
            required=False,
            description="Editable en cualquier status; null = quitar (solo borrador)",
        ),
    },
)

quizz_model_status_model = api.model(
    "QuizzModelStatus",
    {
        "status": fields.Integer(
            required=True,
            description="0=borrador 1=activa 2=archivada. Transiciones: 0->1, 1->2, 2->1",
            example=1,
        ),
    },
)


class QuizzModelPostForm(Form):
    name = StringField("name", validators=[InputRequired()])


class QuizzModelPutForm(Form):
    name = StringField("name", [], default=None)


class QuizzModelStatusForm(Form):
    status = IntegerField("status", validators=[InputRequired()])
