# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/may./2024  at 11:21 $"

from flask_restx import fields
from wtforms.fields.datetime import DateField, DateTimeField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.simple import EmailField

from static.Models.api_models import date_filter, datetime_filter
from static.constants import api
from wtforms.validators import InputRequired
from wtforms import IntegerField, StringField
from wtforms.form import Form

employee_model = api.model(
    "Employee",
    {
        "id": fields.Integer(required=True, description="The employee id"),
        "name": fields.String(required=True, description="The employee name"),
        "lastname": fields.String(required=True, description="The employee lastname"),
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
    "EmployeeInfo", {
        "data": fields.List(fields.Nested(employee_model)),
        "error": fields.String(required=False, description="The error message")
    }
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
    "EmployesExamenes", {
        "data": fields.List(fields.Nested(examenes_medicos_model)),
        "error": fields.String(required=False, description="The error message")
    }
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
        "status": fields.String(
            required=True, description="The vacation prime status", example="Si"
        ),
        "fecha_pago": fields.String(
            required=True, description="The employee name", example="2Q JUL 23"
        ),
    },
)

seniority_dict_model = api.model(
    "SeniorityDict",
    {
        "year": fields.Integer(required=True, description="The year"),
        "prima": fields.Nested(prima_vacation_model),
        "status": fields.String(
            required=True, description="The status of days taken", example="7 PTES"
        ),
        "comentarios": fields.String(required=True, description="Any comentary"),
    },
)

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
    "EmployeesVacations", {
        "data": fields.List(fields.Nested(vacations_model)),
        "error": fields.String(required=False, description="The error message")
    }
)

employee_vacation_model_insert = api.model(
    "EmployeeVacationInsert",
    {
        "emp_id": fields.Integer(required=True, description="The employee id"),
        "seniority": fields.List(
            fields.Nested(seniority_dict_model),
            required=True,
            description="The employee seniority",
        ),
    },
)


employee_vacation_model_delete = api.model(
    "EmployeeVacationDelete",
    {"emp_id": fields.Integer(required=True, description="The employee id")},
)


class EmployeeInputForm(Form):
    name = StringField("name", validators=[InputRequired()])
    lastname = StringField("lastname", validators=[InputRequired()])
    phone = StringField("phone", validators=[InputRequired()])
    dep = IntegerField("dep", validators=[InputRequired()])
    modality = StringField("modality", validators=[InputRequired()])
    email = StringField("email", validators=[InputRequired()])
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
    info = FormField(EmployeeInputForm, "info")


class EmployeeUpdateForm(Form):
    id = IntegerField(
        "id",
        validators=[InputRequired(message="id is required or value 0 not accepted")],
    )
    info = FormField(EmployeeInputForm, "info")


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


class PrimaVacForm(Form):
    status = StringField("status", validators=[], default="No")
    fecha_pago = DateField(
        "fecha_pago", validators=[InputRequired()], filters=[date_filter]
    )


class SeniorityForm(Form):
    prima = FormField(PrimaVacForm, "prima")
    status = StringField("status", validators=[InputRequired()])
    comentarios = StringField("comentarios", validators=[], default="")


class EmployeeVacInsertForm(Form):
    emp_id = IntegerField(
        "emp_id",
        validators=[InputRequired(message="id is required or value 0 not accepted")],
    )
    seniority = FieldList(FormField(SeniorityForm), "seniority")


class DeleteVacationForm(Form):
    emp_id = IntegerField(
        "emp_id",
        validators=[InputRequired(message="id is required or value 0 not accepted")],
    )
