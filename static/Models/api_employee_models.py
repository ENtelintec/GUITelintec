# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/may./2024  at 11:21 $"

from flask_restx import fields
from wtforms.fields.datetime import DateField, DateTimeField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.simple import EmailField

from static.extensions import api, format_date, format_timestamps
from wtforms.validators import InputRequired
from wtforms import IntegerField, StringField
from wtforms.form import Form

employee_model = api.model(
    "Employee",
    {
        "id": fields.Integer(required=True, description="The employee id"),
        "name": fields.String(required=True, description="The employee name"),
        "phone": fields.String(required=True, description="The employee phone number"),
        "dep": fields.String(required=True, description="The employee department"),
        "modality": fields.String(required=True, description="The employee modality"),
        "email": fields.String(
            required=True,
            description="The employee email",
            example="example@example.com",
        ),
        "contract": fields.String(required=True, description="The employee contract"),
        "admission": fields.String(
            required=True,
            description="The employee admission date",
            example="2024-03-01",
        ),
        "rfc": fields.String(required=True, description="The employee rfc"),
        "curp": fields.String(required=True, description="The employee curp"),
        "nss": fields.String(required=True, description="The employee nss"),
        "emergency": fields.String(
            required=True,
            description="The employee emergency contact",
            example='{"name": null, "phone_number": "81 0000 0000"}',
        ),
        "position": fields.String(required=True, description="The employee puesto"),
        "status": fields.String(required=True, description="The employee status"),
        "departure": fields.String(
            required=True,
            description="The employee departure",
            example='{"date": "2024-03-01", "reason": ""}',
        ),
        "exam_id": fields.Integer(required=True, description="The medical examen id"),
        "birthday": fields.String(
            required=True, description="The employee birthday", example="2024-03-01"
        ),
        "legajo": fields.String(required=True, description="The employee legajo"),
    },
)

employee_model_input = api.model(
    "Employee",
    {
        "name": fields.String(required=True, description="The employee name"),
        "lastname": fields.String(required=True, description="The employee lastname"),
        "phone": fields.String(required=True, description="The employee phone number"),
        "dep": fields.Integer(required=True, description="The employee department id"),
        "modality": fields.String(required=True, description="The employee modality"),
        "email": fields.String(required=True, description="The employee email"),
        "contract": fields.String(required=True, description="The employee contract"),
        "admission": fields.String(
            required=True,
            description="The employee admission date",
            example="2024-03-01",
        ),
        "rfc": fields.String(required=True, description="The employee rfc"),
        "curp": fields.String(required=True, description="The employee curp"),
        "nss": fields.String(required=True, description="The employee nss"),
        "emergency": fields.String(
            required=True,
            description="The employee emergency contact",
            example='{"name": null, "phone_number": "81 0000 0000"}',
        ),
        "position": fields.String(required=True, description="The employee puesto"),
        "status": fields.String(required=True, description="The employee status"),
        "departure": fields.String(
            required=True,
            description="The employee departure",
            example='{"date": "2024-03-01", "reason": ""}',
        ),
        "birthday": fields.String(
            required=True, description="The employee birthday", example="2024-03-01"
        ),
        "legajo": fields.String(required=True, description="The employee legajo"),
    },
)

employee_model_update = api.model(
    "Employee update",
    {
        "id": fields.Integer(required=True, description="The employee id", example=60),
        "info": fields.Nested(employee_model_input),
    },
)

employee_model_delete = api.model(
    "Employee delete",
    {"id": fields.Integer(required=True, description="The employee id")},
)

employee_model_insert = api.model(
    "Employee delete all", {"info": fields.Nested(employee_model_input)}
)

employees_info_model = api.model(
    "EmployeeInfo", {"data": fields.List(fields.Nested(employee_model))}
)

examenes_medicos_model = api.model(
    "ExamenesMedicos",
    {
        "exist": fields.Boolean(required=True, description="The exist"),
        "id_exam": fields.Integer(required=True, description="The id"),
        "name": fields.String(required=True, description="The name"),
        "blood": fields.String(required=True, description="The date"),
        "status": fields.String(required=True, description="The status"),
        "aptitudes": fields.List(
            fields.Integer(required=True, description="The aptitud")
        ),
        "dates": fields.List(fields.String(required=True, description="The date")),
        "apt_actual": fields.Integer(required=True, description="The aptitud"),
        "emp_id": fields.Integer(required=True, description="The id"),
    },
)
exam_med_model_input = api.model(
    "ExamenMedico",
    {
        "name": fields.String(required=True, description="The name"),
        "blood": fields.String(required=True, description="The date"),
        "status": fields.String(required=True, description="The status"),
        "aptitudes": fields.List(
            fields.Integer(required=True, description="The aptitud")
        ),
        "dates": fields.List(fields.String(required=True, description="The date")),
        "apt_actual": fields.Integer(required=True, description="The aptitud"),
        "emp_id": fields.Integer(required=True, description="The id"),
    },
)

employees_examenes_model = api.model(
    "EmployesExamenes", {"data": fields.List(fields.Nested(examenes_medicos_model))}
)

employee_exam_model_insert = api.model(
    "EmployesExamenInsert", {"info": fields.Nested(exam_med_model_input)}
)

employee_exam_model_update = api.model(
    "EmployesExameneUpdate",
    {
        "id": fields.Integer(required=True, description="The medical exam id"),
        "info": fields.Nested(exam_med_model_input),
    },
)

employee_exam_model_delete = api.model(
    "EmployesExameneDelete",
    {"id": fields.Integer(required=True, description="The medical exam  id")},
)

prima_vacation_model = api.model(
    "PrimaVacation",
    {
        "status": fields.String(required=True, description="The vacation prime status"),
        "fecha_pago": fields.String(
            required=True, description="The employee name", example="2Q JUL 23"
        ),
    },
)

status_vacation_model = api.model(
    "StatusVacation",
    {
        "prima": fields.Nested(prima_vacation_model),
        "status": fields.String(
            required=True, description="The status of days taken", example="7 PTES"
        ),
        "comentarios": fields.String(required=True, description="Any comentary"),
    },
)

seniority_dict_model = api.model("SeniorityDict", {"0": fields.Nested(employee_model)})

vacations_model = api.model(
    "Vacations",
    {
        "emp_id": fields.Integer(required=True, description="The employee id"),
        "name": fields.String(required=True, description="The employee name"),
        "date_admission": fields.String(
            required=True,
            description="The employee admission date",
            example="2024-03-01",
        ),
        "seniority": fields.Raw(required=True, description="The employee seniority"),
    },
)

employees_vacations_model = api.model(
    "EmployeesVacations", {"data": fields.List(fields.Nested(vacations_model))}
)

employee_vacation_model_insert = api.model(
    "EmployeeVacationInsert",
    {
        "emp_id": fields.Integer(required=True, description="The employee id"),
        "seniority": fields.Nested(
            seniority_dict_model,
            example={
                "0": {
                    "prima": {"status": "SI", "fecha_pago": "2Q JUL 23"},
                    "status": "7 PTES",
                    "comentarios": "31 ago 23\n29 sep 23\n27 dic 23 - 29 dic 23",
                }
            },
        ),
    },
)
employee_vacation_model_delete = api.model(
    "EmployeeVacationDelete",
    {"emp_id": fields.Integer(required=True, description="The employee id")},
)


def date_filter(date):
    # Example filter function to format the date
    return date.strftime(format_date) if not isinstance(date, str) else date


def datetime_filter(date):
    # Example filter function to format the date
    return date.strftime(format_timestamps) if not isinstance(date, str) else date


class EmployeeInputForm(Form):
    name = StringField("name", validators=[InputRequired()])
    lastname = StringField("lastname", validators=[InputRequired()])
    phone = StringField("phone", validators=[InputRequired()])
    dep = IntegerField("dep", validators=[InputRequired()])
    modality = StringField("modality", validators=[InputRequired()])
    email = EmailField("email", validators=[InputRequired()])
    contract = StringField("contract", validators=[InputRequired()])
    admission = DateField(
        "admission", validators=[InputRequired()], filters=[date_filter]
    )
    rfc = StringField("rfc", validators=[InputRequired()])
    curp = StringField("curp", validators=[InputRequired()])
    nss = StringField("nss", validators=[InputRequired()])
    emergency = StringField("emergency", validators=[InputRequired()])
    position = StringField("position", validators=[InputRequired()])
    status = StringField("status", validators=[InputRequired()])
    departure = StringField("departure", validators=[InputRequired()])
    birthday = DateField(
        "birthday", validators=[InputRequired()], filters=[date_filter]
    )
    legajo = StringField("legajo", validators=[InputRequired()])


class EmployeeInsertForm(Form):
    info = FormField(EmployeeInputForm)


class EmployeeUpdateForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="id is required or value 0 not accepted")],
    )
    info = FormField(EmployeeInputForm)


class EmployeeDeleteForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="id is required or value 0 not accepted")],
    )


class AptitudForm(Form):
    aptitude = IntegerField("aptitude", default=1)


class DateExam(Form):
    date = DateTimeField("date", filters=[datetime_filter])


class EmployeeMedForm(Form):
    name = StringField("name", validators=[InputRequired()])
    blood = StringField("blood", validators=[InputRequired()])
    status = StringField("status", validators=[InputRequired()])
    aptitudes = FieldList(FormField(AptitudForm), "aptitudes")
    dates = FieldList(FormField(DateExam), "dates")
    apt_actual = IntegerField("apt_actual", validators=[], default=1)
    emp_id = IntegerField(
        "emp_id",
        validators=[InputRequired(message="id is required or value 0 not accepted")],
    )


class EmployeeMedInsertForm(Form):
    info = FormField(EmployeeMedForm, "info")


class EmployeeMedUpdateForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="id is required or value 0 not accepted")],
    )
    info = FormField(EmployeeMedForm, "info")


class EmployeeMedDeleteForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="id is required or value 0 not accepted")],
    )
