# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 05/ago./2026  at 12:00 $"

from flask_restx import fields
from wtforms import BooleanField, IntegerField, StringField
from wtforms.form import Form
from wtforms.validators import InputRequired, Optional

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
            required=False,
            description="Editable mientras el tipo no tenga encuestas asignadas (tasks_total = 0); con encuestas -> clonar",
        ),
        "rubric": fields.Raw(
            required=False,
            description="Editable en cualquier status; null = quitar (solo sin encuestas asignadas)",
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
        "migrate_pending": fields.Boolean(
            required=False,
            default=False,
            description=(
                "Solo al publicar (0->1) una versión clonada (replaces): además de archivar "
                "la versión anterior, reapunta sus encuestas PENDIENTES a esta versión"
            ),
        ),
    },
)

quizz_model_clone_model = api.model(
    "QuizzModelClone",
    {
        "name": fields.String(
            required=False,
            description="Nombre de la versión nueva (default: '<nombre> (v2)', o v3, v4...)",
            example="Encuesta de clima laboral (v2)",
        ),
    },
)

quizz_model_migrate_model = api.model(
    "QuizzModelMigrateTasks",
    {
        "from_type": fields.Integer(
            required=True, description="type_q de la versión vieja cuyas encuestas pendientes se mueven", example=3
        ),
        "only_pending": fields.Boolean(
            required=False,
            default=True,
            description="v1 solo acepta true: las contestadas y las de eva 360 nunca se migran",
        ),
    },
)


class QuizzModelPostForm(Form):
    name = StringField("name", validators=[InputRequired()])


class QuizzModelPutForm(Form):
    name = StringField("name", [], default=None)


class QuizzModelStatusForm(Form):
    status = IntegerField("status", validators=[InputRequired()])
    migrate_pending = BooleanField("migrate_pending", validators=[Optional()], default=False)


class QuizzModelCloneForm(Form):
    name = StringField("name", [], default=None)


class QuizzModelMigrateForm(Form):
    from_type = IntegerField("from_type", validators=[InputRequired()])
    # `only_pending` NO se modela aqui: un BooleanField ausente vale False y
    # el default debe ser true; el midleware lo lee del payload crudo.
