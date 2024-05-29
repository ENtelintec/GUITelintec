# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 13/feb./2024  at 15:36 $"

import json
from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from static.extensions import quizzes_RRHH, quizz_out_path, format_date
from templates.Funtions_Utils import (
    create_Combobox,
    create_label,
)
from templates.controllers.employees.employees_controller import get_id_name_employee
from templates.modules.RRHH.SubFrame_QuizzMaker import QuizMaker


def get_name_id_employees_list(
        department: int, is_all: bool) -> tuple[list[str], list[tuple[str, int, str, str, dict]]]:
    flag, error, out = get_id_name_employee(department, is_all)
    names = []
    aux = []
    for id_emp, name, lastname, job, date_admission, departure in out:
        names.append(f"{name.upper()} {lastname.upper()}")
        if departure is None:
            departure = {"date": "not defined", "reason": ""}
        else:
            departure = json.loads(departure)
        job = job.upper() if job is not None else "other"
        aux.append(
            (
                f"{name.upper()} {lastname.upper()}",
                id_emp,
                job,
                date_admission,
                departure,
            )
        )
    return names, aux


class FrameEncuestas(ttk.Frame):
    def __init__(
            self, master, quizzes=quizzes_RRHH, quizz_out=None, interviewer="default", setting: dict = None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        # ----------Title-------------
        ttk.Label(self, text="Encuestas", font=("Helvetica", 30, "bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="nswe"
        )
        self.username_data = kwargs.get("username_data")
        # ----------variables-------------
        self.quizz_out_path = quizz_out_path if quizz_out is None else quizz_out
        self.quizzes = quizzes
        self.quizz = None
        self.dict_quizz = None
        self.filepath = None
        self.tipo_id = None
        if "name" not in self.username_data or "lastname" not in self.username_data:
            self.interviewer = "default"
        else:
            self.interviewer = self.username_data["name"].upper() + " " + self.username_data["lastname"].upper()
        # ----------widgets-------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        frame_inputs.columnconfigure((0, 1), weight=1)
        options = []
        for item in self.quizzes.values():
            options.append(item["name"])
        self.quizz_selector = create_Combobox(frame_inputs, values=options, state="readonly", row=0, column=0,
                                              sticky="n", width=50, columnspan=2)
        self.quizz_selector.bind("<<ComboboxSelected>>", self.select_quiz)
        self.quizz_selector.set("Seleccione una encuesta")
        # employee making the quizz data
        self.names, self.emps_metadata = get_name_id_employees_list(1, True) if "encuestas" not in kwargs[
            "data"] else (
            kwargs["data"]["encuestas"]["names"], kwargs["data"]["encuestas"]["emps_metadata"])
        create_label(
            frame_inputs, text="Empleado encuestado: ", row=1, column=0, sticky="w"
        )
        self.name_emp_selector = create_Combobox(frame_inputs, values=self.names, state="readonly", width=40, row=1,
                                                 column=1, sticky="w")
        # evaluated employee
        self.label_evaluated = create_label(
            frame_inputs, text="Empleado evaluado: ", row=0, column=2, sticky="w")
        self.label_evaluated.grid_remove()
        self.name_emp_evaluated = create_Combobox(frame_inputs, values=self.names, state="readonly", width=40, row=0,
                                                  column=3, sticky="w")
        self.name_emp_evaluated.grid_remove()
        self.label_pos_evaluator = create_label(
            frame_inputs, text="Nivel del evaluado: ", row=1, column=2, sticky="w")
        self.label_pos_evaluator.grid_remove()
        self.pos_evaluator = create_Combobox(frame_inputs,
                                             values=["Autoevaluación", "Jefe Inmediato", "Colega", "Subordinado"],
                                             state="readonly", width=40, row=1, column=3, sticky="w")
        self.pos_evaluator.grid_remove()
        # ------------buttons------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=2, column=0, padx=10, pady=10, sticky="nswe")
        frame_btns.columnconfigure(0, weight=1)
        # noinspection PyArgumentList
        ttk.Button(
            frame_btns,
            text="Crear Encuesta",
            command=self.create_quiz,
            width=20,
            bootstyle="primary",
        ).grid(row=0, column=0, padx=10, pady=10, sticky="n")
        # ----------encuestas--------
        self.frame_encuesta = ttk.Frame(self)
        self.frame_encuesta.grid(row=3, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_encuesta.columnconfigure(0, weight=1)
        self.frame_encuesta.rowconfigure(0, weight=1)

    def select_quiz(self, event=None):
        quiz_name = event.widget.get()
        flag = False
        for item in self.quizzes.values():
            if item["name"] == quiz_name:
                self.filepath = item["path"]
                flag = True
                self.dict_quizz = json.load(open(self.filepath, encoding="utf-8"))
                self.tipo_id = item["type"]
                if self.tipo_id == 4:
                    self.label_evaluated.grid()
                    self.name_emp_evaluated.grid()
                    self.label_pos_evaluator.grid()
                    self.pos_evaluator.grid()
                else:
                    self.label_evaluated.grid_remove()
                    self.name_emp_evaluated.grid_remove()
                    self.label_pos_evaluator.grid_remove()
                    self.pos_evaluator.grid_remove()
                break
        if not flag:
            self.filepath = None
            self.dict_quizz = None
            self.quizz = None

    def create_quiz(self):
        if self.dict_quizz is None or self.name_emp_selector.get() == "":
            return
        else:
            msg = f"Esta seguro que desea crear la encuesta para {self.name_emp_selector.get()}?"
            answer = Messagebox.show_question(title="Confirmacion", message=msg)
            if answer == "No":
                return
        print("creating quizz")
        data_emp_questioned = None
        for row in self.emps_metadata:
            if row[0] == self.name_emp_selector.get():
                data_emp_questioned = row
                break
        data_emp_evaluated = None
        for row in self.emps_metadata:
            if row[0] == self.name_emp_evaluated.get():
                data_emp_evaluated = row
                break
        metadata = {
            "name_emp": self.name_emp_selector.get(),
            "date": datetime.now().strftime(format_date),
            "interviewer": self.interviewer,
            "ID_emp": data_emp_questioned[1],
            "position": data_emp_questioned[2],
            "admision": data_emp_questioned[3],
            "departure": data_emp_questioned[4]["date"],
            "departure_reason": data_emp_questioned[4]["reason"],
            "evaluated_emp": self.name_emp_evaluated.get(),
            "pos_evaluator": self.pos_evaluator.get(),
            "evaluated_emp_ID": data_emp_evaluated[1]
        }
        name_quizz = self.quizz_selector.get()
        self.dict_quizz = json.load(open(self.filepath, encoding="utf-8"))

        QuizMaker(
            self.dict_quizz,
            title=name_quizz,
            tipo_id=self.tipo_id,
            out_path=self.quizz_out_path,
            metadata=metadata
        )
