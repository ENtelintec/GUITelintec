# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/nov./2023  at 17:32 $"

from static.extensions import api, format_timestamps
from flask_restx import fields
from wtforms.fields.datetime import DateTimeField
from wtforms.validators import InputRequired
from wtforms import FormField, IntegerField, StringField, validators
from wtforms.fields.list import FieldList
from wtforms.form import Form

permission_model = api.model(
    "Permission",
    {
        "name": fields.String(required=True, description="The name"),
        "description": fields.String(required=True, description="The description"),
    },
)


class ResumeModelForm(Form):
    id = IntegerField("id", validators=[validators.input_required()])
    name = StringField("name", validators=[validators.input_required()])
    contract = StringField("contract", validators=[validators.input_required()])
    absences = IntegerField("absences", validators=[validators.input_required()])
    late = IntegerField("late", validators=[validators.input_required()])
    total_late = IntegerField("total_late", validators=[validators.input_required()])
    extra = IntegerField("extra", validators=[validators.input_required()])
    total_h_extra = IntegerField(
        "total_h_extra", validators=[validators.input_required()]
    )
    primes = IntegerField("primes", validators=[validators.input_required()])
    absences_details = StringField(
        "absences_details", validators=[validators.input_required()]
    )
    late_details = StringField("late_details", validators=[validators.input_required()])
    extra_details = StringField(
        "extra_details", validators=[validators.input_required()]
    )
    primes_details = StringField(
        "primes_details", validators=[validators.input_required()]
    )
    normals_details = StringField(
        "normals_details", validators=[validators.input_required()]
    )
    earlies_details = StringField(
        "earlies_details", validators=[validators.input_required()]
    )
    pasives_details = StringField(
        "pasives_details", validators=[validators.input_required()]
    )


resume_model = api.model(
    "Resume",
    {
        "id": fields.Integer(required=True, description="The id"),
        "name": fields.String(required=True, description="The name"),
        "contract": fields.String(required=True, description="The contract"),
        "absences": fields.Integer(required=True, description="The absences"),
        "late": fields.Integer(required=True, description="The late"),
        "total_late": fields.Integer(required=True, description="The total late"),
        "extra": fields.Integer(required=True, description="The extra"),
        "total_h_extra": fields.Integer(required=True, description="The total"),
        "primes": fields.Integer(required=True, description="The primes"),
        "absences_details": fields.String(
            required=True, description="The absences details"
        ),
        "late_details": fields.String(required=True, description="The late details"),
        "extra_details": fields.String(required=True, description="The extra details"),
        "primes_details": fields.String(
            required=True, description="The primes details"
        ),
        "normals_details": fields.String(
            required=True, description="The normals details"
        ),
        "earlies_details": fields.String(
            required=True, description="The early data details"
        ),
        "pasives_details": fields.String(
            required=True, description="The pasives details"
        ),
    },
)


employees_resume_model = api.model(
    "EmployeesResume",
    {
        "data": fields.List(fields.Nested(resume_model)),
    },
)


class EmployeesResumeModelForm(Form):
    data = FieldList(
        FormField(ResumeModelForm), validators=[validators.input_required()]
    )


token_info_model = api.model(
    "TokenInfo",
    {
        "access_token": fields.String(required=True, description="The access token"),
        "expires_in": fields.Integer(
            required=True, description="The number of seconds until the token expires"
        ),
        "timestamp": fields.String(
            required=True, description="The time the token was created"
        ),
        "remaining_time": fields.String(
            required=True, description="The number of seconds until the token expires"
        ),
    },
)

token_permissions_model = api.model(
    "TokenPermissions",
    {"token": fields.String(required=True, description="The access token")},
)

permissions_answer = api.model(
    "PermissionsAnswer",
    {
        "permissions": fields.String(required=True, description="The permissions"),
        "username": fields.String(required=True, description="The username"),
        "error": fields.String(required=False, description="The error"),
    },
)
expected_headers_per = api.parser()
expected_headers_per.add_argument("Authorization", location="headers", required=True)

expected_headers_bot = api.parser()
expected_headers_bot.add_argument("Authorization", location="headers", required=True)


notification_model = api.model(
    "Notification",
    {
        "id": fields.Integer(
            required=False, description="The id on the DB (only for answer)"
        ),
        "title": fields.String(required=True, description="The title"),
        "msg": fields.String(
            required=True, description="The message of the notification"
        ),
        "status": fields.Integer(required=True, description="The status"),
        "sender_id": fields.Integer(required=True, description="The sender id"),
        "timestamp": fields.String(
            required=True, description="The timestamp", example="2024-04-30 17:48:26"
        ),
        "receiver_id": fields.Integer(required=True, description="The receiver id"),
        "app": fields.List(
            fields.String(required=True, description="The app"),
            example=["app1", "app2"],
        ),
    },
)

notification_request_model = api.model(
    "NotificationRequest",
    {
        "data": fields.List(fields.Nested(notification_model)),
        "msg": fields.String(required=True, description="The message from the server"),
    },
)

notification_insert_model = api.model(
    "NotificationInputAMC",
    {
        "info": fields.Nested(
            notification_model, description="The notification info to insert"
        ),
        "id": fields.Integer(
            required=True,
            description="The notification id to modify, only required in update",
        ),
    },
)

notification_delete_model = api.model(
    "NotificationDeleteAMC",
    {"id": fields.Integer(required=True, description="The notification id to delete")},
)


response_av_model = api.model(
    "ResponseAV",
    {
        "answer": fields.String(
            required=True, description="The message from the server"
        ),
        "files": fields.List(fields.String(required=True, description="The files")),
        "id": fields.Integer(required=True, description="The id of the av chat"),
    },
)

request_av_response_model = api.model(
    "RequestAVResponse",
    {
        "msg": fields.String(required=True, description="The message to the server"),
        "department": fields.String(required=True, description="The department"),
        "filename": fields.String(
            required=True, description="The name of the file to use with the av"
        ),
        "files": fields.List(
            fields.String(
                required=True, description="The files the av use including <filename>"
            )
        ),
        "id": fields.Integer(required=False, description="The id of the av chat"),
    },
)

files_av_model = api.model(
    "ResponseFilesAV",
    {
        "path": fields.String(required=True, description="The path of the file"),
        "name": fields.String(required=False, description="The name of the file"),
        "file_openai": fields.String(
            required=False, description="The file id of the openai"
        ),
        "file_id": fields.String(
            required=False, description="The file id of the assistat"
        ),
        "department": fields.String(required=True, description="The department"),
        "status": fields.String(required=True, description="The status of the file"),
    },
)
response_files_av_model = api.model(
    "ResponseFilesAV",
    {
        "files": fields.List(fields.Nested(files_av_model)),
    },
)


def datetime_filer(datetime_obj):
    return (
        datetime_obj.strftime(format_timestamps)
        if not isinstance(datetime_obj, str)
        else datetime_obj
    )


class NotificationForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="id required or value 0 not accepted")]
    )
    title = StringField("title", validators=[InputRequired()])
    msg = StringField("msg", validators=[InputRequired()])
    status = IntegerField("status", validators=[], default=0)
    sender_id = IntegerField("sender_id", validators=[], default=0)
    timestamp = DateTimeField(
        "timestamp", validators=[InputRequired()], filters=[datetime_filer]
    )
    receiver_id = IntegerField("receiver_id", validators=[], default=0)
    app = FieldList(StringField(), validators=[], default=[])


class NotificationInsertForm(Form):
    info = FormField(NotificationForm)
    id = IntegerField(
        "id", validators=[InputRequired(message="id required or value 0 not accepted")]
    )


class NotificationDeleteForm(Form):
    id = IntegerField(
        "id", validators=[InputRequired(message="id required or value 0 not accepted")]
    )


class RequestAVResponseForm(Form):
    msg = StringField("msg", validators=[InputRequired()])
    department = StringField("department", validators=[InputRequired()])
    filename = StringField("filename", validators=[InputRequired()])
    files = FieldList(StringField(), validators=[], default=[])
    id = IntegerField("id", validators=[], default=0)
