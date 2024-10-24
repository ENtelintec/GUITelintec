# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/abr./2024  at 9:53 $"

import csv
from datetime import datetime

from flask import send_file
from flask_restx import Resource, Namespace

from static.Models.api_fichaje_models import (
    fichaje_request_model,
    fichaje_add_update_request_model,
    fichaje_delete_request_model,
    bitacora_dowmload_report_model,
    FichajeRequestFormr,
    FichajeAddUpdateRequestForm,
    FichajeDeleteRequestForm,
    BitacoraDownloadReportForm,
    FichajeRequestMultipleEvents_model,
    FichajeRequestMultipleEvents,
    FichajeRequestExtras_model,
    FichajeRequestExtras, FichajeAproveExtras_model, FichajeAproveExtras,
)
from static.Models.api_sm_models import client_emp_sm_response_model
from static.extensions import (
    delta_bitacora_edit,
    format_date,
    format_timestamps,
    filepath_bitacora_download,
    log_file_bitacora_path,
)
from templates.misc.Functions_AuxFiles import (
    get_events_op_date,
    update_bitacora,
    update_bitacora_value,
    erase_value_bitacora,
)
from templates.misc.Functions_Files import write_log_file
from templates.Functions_Utils import create_notification_permission
from templates.resources.midleware.Functions_DB_midleware import check_date_difference
from templates.controllers.employees.employees_controller import (
    get_employees_op_names,
    get_contracts_operaciones,
)
from templates.resources.midleware.Functions_midleware_misc import (
    get_events_from_extraordinary_sources,
)
from templates.resources.midleware.MD_Bitacora import get_events_extra, add_aproved_to_comment

ns = Namespace("GUI/api/v1/bitacora")


@ns.route("/employees")
class Employees(Resource):
    @ns.marshal_with(client_emp_sm_response_model)
    def get(self):
        flag, error, result = get_employees_op_names()
        if flag:
            return {"data": result, "comment": error}, 200
        else:
            return {"data": result, "comment": error}, 400


@ns.route("/fichaje/table")
class FichajeTable(Resource):
    @ns.expect(fichaje_request_model)
    def post(self):
        validator = FichajeRequestFormr.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        # code, data = parse_data(ns.payload, 9)
        # if code == 400:
        #     return {"answer": "The data has a bad structure"}, code
        date = data["date"]
        date = datetime.strptime(date, format_date) if isinstance(date, str) else date
        events, columns = get_events_op_date(date, True, emp_id=data["emp_id"])
        return {"data": events, "columns": columns}, 200


@ns.route("/fichaje/event")
class FichajeEvent(Resource):
    @ns.expect(fichaje_add_update_request_model)
    def post(self):
        validator = FichajeAddUpdateRequestForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        out = check_date_difference(data["date"], delta_bitacora_edit)
        flag = False
        error = None
        events_added = []
        if not out:
            return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
        if data["event"].lower() == "extraordinary":
            event, data_events = get_events_from_extraordinary_sources(
                data["hour_in"], data["hour_out"], data
            )
            for index, item in enumerate(data_events):
                flag, error, result = update_bitacora(
                    data["id_emp"], event[index], item
                )
                if flag:
                    events_added.append(f"{event[index]}_{item[1]}, result: {result}")
        else:
            flag, error, result = update_bitacora(
                data["id_emp"],
                data["event"],
                (data["date"], data["value"], data["comment"], data["contract"]),
            )
            if flag:
                events_added.append(
                    f"{data['event']}_{data['value']}, result: {result}"
                )
        if flag:
            msg = (
                f"Record inserted-->Por: {data['id_leader']}, para empleado: {data['id_emp']}, Fecha: {data['date']}, "
                f"Evento: {data['event']}, Valor: {data['value']}, Comentario: {data['comment']}"
            )
            create_notification_permission(
                msg,
                ["bitacora", "operaciones"],
                "Nuevo evento bitacora",
                data["id_leader"],
                data["id_emp"],
            )
            write_log_file(log_file_bitacora_path, msg)
            return {"answer": "The event has been added", "data": events_added}, 201
        elif error is not None:
            print(error)
            return {"answer": "There has been an error at adding the bitacora"}, 404
        else:
            return {"answer": "Fail to add registry"}, 404

    @ns.expect(fichaje_add_update_request_model)
    def put(self):
        validator = FichajeAddUpdateRequestForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        # code, data = parse_data(ns.payload, 10)
        # if code == 400:
        #     return {"answer": "The data has a bad structure"}, code
        out = check_date_difference(data["date"], delta_bitacora_edit)
        if not out:
            return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
        flag, error, result = update_bitacora_value(
            data["id_emp"],
            data["event"],
            (data["date"], data["value"], data["comment"], data["contract"]),
        )
        if flag:
            msg = (
                f"Record updated-->Por: {data['id_leader']}, para empleado: {data['id_emp']}, Fecha: {data['date']}, "
                f"Evento: {data['event']}, Valor: {data['value']}, Comentario: {data['comment']}"
            )
            create_notification_permission(
                msg,
                ["bitacora", "operaciones"],
                "Evento bitacora actualizado",
                data["id_leader"],
                data["id_emp"],
            )
            write_log_file(log_file_bitacora_path, msg)
            return {"answer": "The event has been updated"}, 200
        elif error is not None:
            print(error)
            return {"answer": "There has been an error at updating the bitacora"}, 404
        else:
            return {"answer": "Fail to update registry"}, 404

    @ns.expect(fichaje_delete_request_model)
    def delete(self):
        validator = FichajeDeleteRequestForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        # code, data = parse_data(ns.payload, 11)
        # if code == 400:
        #     return {"answer": "The data has a bad structure"}, code
        out = check_date_difference(data["date"], delta_bitacora_edit)
        if not out:
            return {"answer": "No se puede alterar la bitcaora en esta fecha."}, 403
        flag, error, result = erase_value_bitacora(
            data["id_emp"], data["event"], (data["date"], data["contract"])
        )
        if flag:
            msg = (
                f"Record deleted-->Por: {data['id_leader']}, para empleado: {data['id_emp']}, Fecha: {data['date']}, "
                f"Evento: {data['event']}"
            )
            create_notification_permission(
                msg,
                ["bitacora", "operaciones"],
                "Evento bitacora eliminado",
                data["id_leader"],
                data["id_emp"],
            )
            write_log_file(log_file_bitacora_path, msg)
            return {"answer": "The event has been deleted"}, 200
        elif error is not None:
            print(error)
            return {"answer": "There has been an error at deleting the bitacora"}, 404
        else:
            return {"answer": "Fail to delete registry"}, 404


@ns.route("/dowload/report")
class BitacoraDownloadReport(Resource):
    @ns.expect(bitacora_dowmload_report_model)
    def post(self):
        validator = BitacoraDownloadReportForm.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        # code, data = parse_data(ns.payload, 14)
        # if code == 400:
        #     return {"answer": "The data has a bad structure"}, code
        date = data["date"]
        date = datetime.strptime(date, format_date) if isinstance(date, str) else date
        events, columns = get_events_op_date(date, False, emp_id=data["id_emp"])
        event_filtered = []
        match data["span"]:
            case "day":
                for item in events:
                    if datetime.strptime(item[7], format_timestamps).day == date.day:
                        event_filtered.append(item)
            case "week":
                for item in events:
                    if (
                        datetime.strptime(item[7], format_timestamps).isocalendar()[1]
                        == date.isocalendar()[1]
                    ):
                        event_filtered.append(item)
            case "month":
                for item in events:
                    if (
                        datetime.strptime(item[7], format_timestamps).month
                        == date.month
                    ):
                        event_filtered.append(item)
        # save csv
        with open(filepath_bitacora_download, "w") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            for item in event_filtered:
                writer.writerow(item)
        # data_out = transform_bitacora_data_to_dict(event_filtered, columns)
        try:
            return send_file(filepath_bitacora_download, as_attachment=True)
        except Exception as e:
            return {"data": f"Error en el tipo de quizz: {str(e)}"}, 400


@ns.route("/contract_list")
class BitacoraEmployeesList(Resource):
    def get(self):
        flag, error, result = get_contracts_operaciones()
        # filtering unique contracts
        contracts = list(set([item[0] for item in result]))
        contracts.sort()
        if flag:
            return {"data": contracts, "comment": error}, 200
        else:
            return {"data": [contracts], "comment": error}, 400


@ns.route("/fichaje/multiple")
class FichajeMultipleEvent(Resource):
    @ns.expect(FichajeRequestMultipleEvents_model)
    def post(self):
        validator = FichajeRequestMultipleEvents.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        events_recieved = data["events"]
        events_added = []
        msg = f"---Agregando nuevos eventos por el lider {data['id_leader']}---"
        for event in events_recieved:
            if event["event"].lower() == "extraordinary":
                event_e, data_events = get_events_from_extraordinary_sources(
                    event["hour_in"], event["hour_out"], event
                )
                for index, item in enumerate(data_events):
                    flag, error, result = update_bitacora(
                        event["id_emp"], event_e[index], item
                    )
                    if flag:
                        events_added.append(
                            f"id_emp: {event['id_emp']}, {event_e[index]}_{item[1]}, flag: {flag}, error: {str(error)}, result: {result}"
                        )
                        msg += f"\nid_emp: {event['id_emp']}, {event_e[index]}_{item[1]}, flag: {flag}, error: {str(error)}, result: {result}"
            else:
                flag, error, result = update_bitacora(
                    event["id_emp"],
                    event["event"],
                    (
                        event["date"],
                        event["value"],
                        event["comment"],
                        event["contract"],
                    ),
                )
                events_added.append(
                    f"id_emp: {event['id_emp']}, {event['event']}_{event['value']}, flag: {flag}, error: {str(error)}, result: {result}"
                )
                msg += f"\nid_emp: {event['id_emp']}, {event['event']}_{event['value']}, flag: {flag}, error: {str(error)}, result: {result}"
        create_notification_permission(
            msg,
            ["bitacora", "operaciones"],
            "Nuevo evento bitacora",
            data["id_leader"],
            data["id_leader"],
        )
        write_log_file(log_file_bitacora_path, msg)
        return {"answer": "The events were proccessed.", "data": events_added}, 200


@ns.route("/fichajes/extra")
class FichajesGetExtra(Resource):
    @ns.expect(FichajeRequestExtras_model)
    def post(self):
        validator = FichajeRequestExtras.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        data, code = get_events_extra(data)
        return {"data": data}, code


@ns.route("/fichajes/extra/aprove")
class FichajesAproveExtra(Resource):
    @ns.expect(FichajeAproveExtras_model)
    def post(self):
        validator = FichajeAproveExtras.from_json(ns.payload)
        if not validator.validate():
            return {"error": validator.errors}, 400
        data = validator.data
        flag, error, result = update_bitacora(
            data["id_emp"],
            "extra",
            [data["date"], data["value"], data["comment"], data["contract"]]
        )
        data["comment"] = add_aproved_to_comment(data["comment"])
        if flag:
            msg = f"Evento extra aprovado: {data['id_emp']}, {data['date']}, {data['value']}, {data['comment']}"
            create_notification_permission(
                msg,
                ["bitacora", "operaciones"],
                "Evento extra aprovado bitacora",
                data["id_leader"],
                data["id_emp"],
            )
            write_log_file(log_file_bitacora_path, msg)
            return {"answer": "The event has been updated"}, 200
        elif error is not None:
            print(error)
            return {"answer": "There has been an error at aproving the bitacora"}, 404
        else:
            return {"answer": "Fail to update registry"}, 404
