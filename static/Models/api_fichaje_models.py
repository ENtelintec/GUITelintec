# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/ago/2024  at 10:38 $"

from flask_restx import fields
from wtforms.fields.datetime import DateField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import FloatField

from wtforms.validators import InputRequired
from wtforms.form import Form
from wtforms import IntegerField, StringField
from static.extensions import api, format_date

fichaje_request_model = api.model(
    "FichajeRequest",
    {
        "date": fields.String(
            required=True, description="Thedate", example="2024-03-01"
        ),
        "emp_id": fields.Integer(
            required=True, description="The id of the employee", example=-1
        ),
    },
)

fichaje_add_update_request_model = api.model(
    "FichajeAddRequest",
    {
        "date": fields.String(
            required=True, description="The date", example="2024-03-01"
        ),
        "event": fields.String(required=True, description="The event", example="falta"),
        "value": fields.Float(required=True, description="The value", example=1.0),
        "comment": fields.String(
            required=True, description="The comment", example="This is a comment"
        ),
        "id_emp": fields.Integer(
            required=True,
            description="The id of employee that has the event",
            example=1,
        ),
        "contract": fields.String(
            required=True, description="The contract of the empployee", example="INFRA"
        ),
        "hour_in": fields.String(
            required=False,
            description="The hour in for extraordinary event",
            example="08:00-->08:15-->8:20",
        ),
        "hour_out": fields.String(
            required=False,
            description="The hour out for extraordinary event",
            example="18:00-->18:15-->18:20",
        ),
        "id_leader": fields.Integer(
            required=True, description="The id of the group leader", example=1
        ),
    },
)

fichaje_post_multiple_request_model = api.model(
    "FichajeAddRequest",
    {
        "date": fields.String(
            required=True, description="The date", example="2024-03-01"
        ),
        "event": fields.String(required=True, description="The event", example="falta"),
        "value": fields.Float(required=True, description="The value", example=1.0),
        "comment": fields.String(
            required=True, description="The comment", example="This is a comment"
        ),
        "id_emp": fields.Integer(
            required=True,
            description="The id of employee that has the event",
            example=1,
        ),
        "contract": fields.String(
            required=True, description="The contract of the empployee", example="INFRA"
        ),
        "hour_in": fields.String(
            required=False,
            description="The hour in for extraordinary event",
            example="08:00-->08:15-->8:20",
        ),
        "hour_out": fields.String(
            required=False,
            description="The hour out for extraordinary event",
            example="18:00-->18:15-->18:20",
        ),
    },
)

fichaje_delete_request_model = api.model(
    "FichajeDeleteRequest",
    {
        "date": fields.String(
            required=True, description="The date", example="2024-03-01"
        ),
        "event": fields.String(required=True, description="The event", example="falta"),
        "id_emp": fields.Integer(
            required=True, description="The id of the editor employee ", example=1
        ),
        "contract": fields.String(
            required=True, description="The contract of the empployee", example="INFRA"
        ),
        "id_leader": fields.Integer(
            required=True, description="The id of the group leader", example=1
        ),
    },
)

bitacora_dowmload_report_model = api.model(
    "BitacoraDownloadReport",
    {
        "date": fields.String(
            required=True, description="The date", example="2024-03-01"
        ),
        "id_emp": fields.Integer(
            required=True,
            description="The id of the employee to require the contract",
            example=-1,
        ),
        "span": fields.String(
            required=True, description="The span of the report", example="month"
        ),
    },
)

FichajeRequestMultipleEvents_model = api.model(
    "FichajeRequestMultipleEvents",
    {
        "events": fields.List(
            fields.Nested(fichaje_post_multiple_request_model), required=True
        ),
        "id_leader": fields.Integer(
            required=True, description="The id of the group leader", example=1
        ),
    },
)


FichajeRequestExtras_model = api.model(
    "FichajeRequestExtras",
    {"date": fields.String(required=True, description="Thedate", example="2024-03-30")},
)


def date_filter(date):
    # Example filter function to format the date
    return date.strftime(format_date) if not isinstance(date, str) else date


class FichajeRequestFormr(Form):
    date = DateField("date", validators=[InputRequired()], filters=[date_filter])
    emp_id = IntegerField(
        "emp_id",
        validators=[InputRequired(message="emp_id is required or 0 not accepted")],
    )


class FichajeAddUpdateRequestForm(Form):
    date = DateField("date", validators=[InputRequired()], filters=[date_filter])
    event = StringField("event", validators=[InputRequired()])
    value = FloatField("value", validators=[InputRequired()])
    comment = StringField("comment", validators=[InputRequired()])
    id_emp = IntegerField(
        "id_emp",
        validators=[InputRequired(message="id_emp is required or 0 not accepted")],
    )
    contract = StringField("contract", validators=[InputRequired()])
    hour_in = StringField("hour_in", default="")
    hour_out = StringField("hour_out", default="")
    id_leader = IntegerField(
        "id_leader",
        validators=[InputRequired(message="id_leader is required or 0 not accepted")],
    )


class FichajePostRequestMultiForm(Form):
    date = DateField("date", validators=[InputRequired()], filters=[date_filter])
    event = StringField("event", validators=[InputRequired()])
    value = FloatField("value", validators=[InputRequired()])
    comment = StringField("comment", validators=[InputRequired()])
    id_emp = IntegerField(
        "id_emp",
        validators=[InputRequired(message="id_emp is required or 0 not accepted")],
    )
    contract = StringField("contract", validators=[InputRequired()])
    hour_in = StringField("hour_in", default="")
    hour_out = StringField("hour_out", default="")


class FichajeDeleteRequestForm(Form):
    date = DateField("date", validators=[InputRequired()], filters=[date_filter])
    event = StringField("event", validators=[InputRequired()])
    id_emp = IntegerField(
        "id_emp",
        validators=[InputRequired(message="id_emp is required or 0 not accepted")],
    )
    contract = StringField("contract", validators=[InputRequired()])
    id_leader = IntegerField(
        "id_leader",
        validators=[InputRequired(message="id_leader is required or 0 not accepted")],
    )


class BitacoraDownloadReportForm(Form):
    date = DateField("date", validators=[InputRequired()], filters=[date_filter])
    id_emp = IntegerField("id_emp", default=-1)
    span = StringField("span", validators=[InputRequired()])


class FichajeRequestMultipleEvents(Form):
    events = FieldList(FormField(FichajePostRequestMultiForm, "events"))
    id_leader = IntegerField(
        "id_leader",
        validators=[InputRequired(message="id_leader is required or 0 not accepted")],
    )


class FichajeRequestExtras(Form):
    date = DateField("date", validators=[InputRequired()], filters=[date_filter])
