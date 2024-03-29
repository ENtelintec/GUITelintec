# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 13/feb./2024  at 15:36 $"

import json
from datetime import datetime
from tkinter import IntVar

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

from static.extensions import quizzes_RRHH, quizz_out_path
from templates.Functions_AuxFiles import save_json_file_quizz
from templates.Functions_SQL import get_id_name_employee
from templates.Funtions_Utils import (
    create_Combobox,
    calculate_results_quizzes,
    create_label,
)
from templates.PDFGenerator import (
    create_pdf__quizz_nor035_v1,
    create_pdf_quizz_nor035_50_plus,
    create_quizz_clima_laboral,
    create_pdf_quizz_salida,
    create_quizz_eva_360,
)


def get_name_id_employees_list(
    department: int, is_all: bool
) -> tuple[list[str], list[tuple[str, int, str, str, dict]]]:
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


class QuizMaker(ttk.Frame):
    def __init__(self, master, dict_quizz, title=None, tipo_id=0, out_path=quizz_out_path, metadata: dict = None):
        super().__init__(master)
        self.quizz_out_path = out_path
        self.q_no = 0
        self.title = title if title is not None else "Quiz"
        self.dict_quizz = dict_quizz
        self.metadata = metadata
        self.questions_label = None
        self.opt_selected = []
        self.data_size = len(self.dict_quizz)
        self.correct = 0
        self.tipo_quizz = tipo_id
        self.last_default = False
        self.questions_default = []
        # ----------widgets-------------
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.display_title()
        self.frame_questions = ttk.Frame(self)
        self.frame_questions.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_questions.columnconfigure(0, weight=1)
        self.frame_questions.rowconfigure(1, weight=1)
        self.frame_options = ScrolledFrame(self.frame_questions, autohide=True)
        self.frame_options.grid(row=1, column=0, padx=20, pady=10, sticky="nswe")
        self.frame_options.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frame_options.rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), weight=1)
        self.frame_buttons = ttk.Frame(self)
        self.frame_buttons.grid(row=3, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_buttons.columnconfigure(0, weight=1)

        # entries
        self.display_question()
        self.entries = self.display_options()
        # buttons
        self.buttons()

    def recreate_frames(self):
        self.frame_questions.destroy()
        self.frame_options.destroy()
        self.frame_questions = ttk.Frame(self)
        self.frame_questions.grid(row=1, column=0, padx=20, pady=10, sticky="nswe")
        self.frame_questions.columnconfigure(0, weight=1)
        self.frame_questions.rowconfigure(1, weight=1)
        self.frame_options = ScrolledFrame(self.frame_questions, autohide=True)
        self.frame_options.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_options.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frame_options.rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), weight=1)

    def display_title(self):
        title = ttk.Label(self, text=self.title, font=("ariel", 20, "bold"))
        title.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    def display_result(self):
        dict_results = calculate_results_quizzes(self.dict_quizz, self.tipo_quizz)
        Messagebox.show_info(
            title="Result",
            message=f"Your final result is:\n"
            f"Calificación final: {dict_results['c_final']}\n"
            f"Calificación de dominio: {dict_results['c_dom']}\n"
            f"Calificacion de categoria: {dict_results['c_cat']}\n",
        )

    def next_btn(self):
        self.save_result()
        self.q_no += 1
        if self.q_no == self.data_size:
            self.display_result()
            self.update_dict_quizz(self.dict_quizz, tipo_op=self.tipo_quizz)
            self.destroy()
        else:
            self.check_especial_case()
            self.recreate_frames()
            self.display_question()
            self.entries = self.display_options()

    def buttons(self):
        # noinspection PyArgumentList
        next_btn = ttk.Button(
            self.frame_buttons,
            text="Next",
            command=self.next_btn,
            width=10,
            bootstyle="primary",
        )
        next_btn.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    def display_question(self):
        if self.questions_label is not None:
            self.questions_label.destroy()
        self.questions_label = ttk.Label(
            self.frame_questions,
            text=self.dict_quizz[str(self.q_no)]["question"],
            font=("ariel", 12, "bold"),
            anchor="n",
        )
        colunmspan = 1
        if self.dict_quizz[str(self.q_no)]["type"] == 3:
            colunmspan = len(self.dict_quizz[str(self.q_no)]["options"]) + 1
        self.questions_label.grid(
            row=0, column=0, columnspan=colunmspan, padx=10, pady=10, sticky="nswe"
        )

    def display_options(self):
        q_list = []
        match self.dict_quizz[str(self.q_no)]["type"]:
            case 1:
                cols = 1
                options = self.dict_quizz[str(self.q_no)]["options"]
                if len(options) > 4:
                    cols = 3
                for index, item in enumerate(options):
                    var = IntVar()
                    index_x = index % cols
                    index_y = index // cols
                    ttk.Checkbutton(
                        self.frame_options,
                        text=item,
                        onvalue=1,
                        offvalue=0,
                        variable=var,
                    ).grid(
                        row=index_y + 1, column=index_x, sticky="w", padx=10, pady=10
                    )
                    q_list.append(var)
            case 2:
                options = self.dict_quizz[str(self.q_no)]["options"]
                q_list.append(IntVar())
                for index, item in enumerate(options):
                    ttk.Radiobutton(
                        self.frame_options, text=item, variable=q_list[-1], value=index
                    ).grid(row=index + 1, column=0, sticky="w", padx=5, pady=5)
            case 3:
                options = self.dict_quizz[str(self.q_no)]["options"]
                subquetions = self.dict_quizz[str(self.q_no)]["subquestions"]
                for index_x, item in enumerate(options):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=1, column=index_x + 1, sticky="n", padx=10, pady=3
                    )
                for index_y, item in enumerate(subquetions):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=index_y + 2, column=0, sticky="w", pady=3
                    )
                    q_list.append(IntVar())
                    index_x = 0
                    for index_x, subitem in enumerate(options):
                        ttk.Radiobutton(
                            self.frame_options,
                            text="",
                            variable=q_list[-1],
                            value=index_x,
                        ).grid(row=index_y + 2, column=index_x + 1, sticky="n", pady=3)
                    if self.last_default and self.q_no in self.questions_default:
                        q_list[-1].set(index_x)
            case 4:
                options = self.dict_quizz[str(self.q_no)]["options"]
                subquetions = self.dict_quizz[str(self.q_no)]["subquestions"]
                for index_x, item in enumerate(options):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=1, column=index_x + 1, sticky="n", padx=10, pady=3
                    )
                for index_y, item in enumerate(subquetions):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=index_y + 2, column=0, sticky="w", pady=3
                    )
                    q_list.append(IntVar())
                    for index_x, subitem in enumerate(options):
                        ttk.Radiobutton(
                            self.frame_options,
                            text="",
                            variable=q_list[-1],
                            value=index_x,
                        ).grid(row=index_y + 2, column=index_x + 1, sticky="n", pady=3)
            case _:
                txt_entry = ttk.Text(self.frame_options, height=4, width=50)
                txt_entry.grid(row=1, column=0, sticky="nswe", padx=10, pady=10)
                q_list.append(txt_entry)
        return q_list

    def save_result(self):
        match self.dict_quizz[str(self.q_no)]["type"]:
            case 1:
                self.opt_selected.append([])
                for i, opt in enumerate(self.entries):
                    if opt.get() == 1:
                        self.opt_selected[-1].append(i)
            case 2:
                self.opt_selected.append(self.entries[0].get())
            case 3:
                self.opt_selected.append([])
                for i, opt in enumerate(self.entries):
                    self.opt_selected[-1].append((i, opt.get()))
            case 4:
                self.opt_selected.append([])
                for i, opt in enumerate(self.entries):
                    self.opt_selected[-1].append((i, opt.get()))
            case _:
                self.opt_selected.append(self.entries[0].get("1.0", "end-1c"))
        self.dict_quizz[str(self.q_no)]["answer"] = self.opt_selected[-1]

    def update_dict_quizz(self, new_dict: dict, tipo_op):
        self.dict_quizz = new_dict
        name_emp = self.metadata["name_emp"]
        id_emp = self.metadata["ID_emp"]
        name_interviewer = self.metadata["interviewer"]
        job = self.metadata["position"]
        terminal = "terminal"
        date_start = str(self.metadata["admision"])
        date_end = str(self.metadata["departure"])
        date_inteview = str(self.metadata["date"])
        file_out = (
            self.quizz_out_path
            + f"{name_emp.replace(' ', '')}_{date_inteview.replace('/', '-')}_type_{tipo_op}.pdf"
        )
        if tipo_op == 0:
            create_pdf_quizz_salida(
                self.dict_quizz, None, file_out, name_emp, job, terminal, date_start, date_end, date_inteview,
                name_interviewer,
            )
        elif tipo_op == 1:
            create_pdf__quizz_nor035_v1(
                self.dict_quizz, None, file_out, name_emp, job, terminal, date_start, date_end, date_inteview,
                name_interviewer
            )
        elif tipo_op == 2:
            create_pdf_quizz_nor035_50_plus(
                self.dict_quizz, None, file_out, name_emp, job, terminal, date_start, date_end, date_inteview,
                name_interviewer
            )
        elif tipo_op == 3:
            # quizz de salida
            create_pdf_quizz_salida(
                self.dict_quizz, None, file_out, name_emp, job, terminal, date_start, date_end, date_inteview,
                name_interviewer
            )
        elif tipo_op == 3:
            create_quizz_clima_laboral(
                self.dict_quizz,
                None,
                file_out,
                name_emp,
                job,
                terminal,
                date_start,
                date_end,
                date_inteview,
                name_interviewer,
            )

        elif tipo_op == 4:
            create_quizz_eva_360(
                self.dict_quizz,
                None,
                file_out,
                name_emp,
                job,
                terminal,
                date_start,
                date_end,
                date_inteview,
                name_interviewer,
            )
            print("create eva360", create_quizz_eva_360)
        print(f"quizz update and pdf generated at {file_out}")
        result_name = f"Quiz_{tipo_op}_{id_emp}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.metadata["date"] = str(self.metadata["date"])
        self.metadata["admision"] = str(self.metadata["admision"])
        self.dict_quizz["metadata"] = self.metadata
        save_json_file_quizz(self.dict_quizz, quizz_out_path + result_name)

    def check_especial_case(self):
        match self.tipo_quizz:
            case 1:
                if self.q_no - 1 == 0:
                    all_no_selected = all(opt == 0 for _, opt in self.opt_selected[-1])
                    self.last_default = not all_no_selected
                    self.questions_default = [1, 2, 3] if not all_no_selected else []
                elif self.q_no - 1 == 10:
                    all_no_selected = all(opt == 0 for _, opt in self.opt_selected[-1])
                    self.last_default = not all_no_selected
                    self.questions_default = [11] if not all_no_selected else []
                elif self.q_no - 1 == 12:
                    all_no_selected = all(opt == 0 for _, opt in self.opt_selected[-1])
                    self.last_default = not all_no_selected
                    self.questions_default = [13] if not all_no_selected else []
            case 2:
                if self.q_no - 1 == 0:
                    all_no_selected = all(opt == 0 for _, opt in self.opt_selected[-1])
                    self.last_default = not all_no_selected
                    self.questions_default = [1, 2, 3] if not all_no_selected else []
                elif self.q_no - 1 == 16:
                    all_no_selected = all(opt == 0 for _, opt in self.opt_selected[-1])
                    self.last_default = not all_no_selected
                    self.questions_default = [17] if not all_no_selected else []
                elif self.q_no - 1 == 18:
                    all_no_selected = all(opt == 0 for _, opt in self.opt_selected[-1])
                    self.last_default = not all_no_selected
                    self.questions_default = [19] if not all_no_selected else []


class FrameEncuestas(ttk.Frame):
    def __init__(
        self,
        master,
        quizzes=quizzes_RRHH,
        quizz_out=None,
        interviewer="default", setting: dict = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        # ----------Title-------------
        ttk.Label(self, text="Encuestas", font=("Helvetica", 30, "bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="nswe"
        )
        # ----------variables-------------
        self.quizz_out_path = quizz_out_path if quizz_out is None else quizz_out
        self.quizzes = quizzes
        self.quizz = None
        self.dict_quizz = None
        self.filepath = None
        self.tipo_id = None
        self.interviewer = interviewer
        # ----------widgets-------------
        frame_inputs = ttk.Frame(self)
        frame_inputs.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        frame_inputs.columnconfigure((0, 1), weight=1)
        options = []
        for item in self.quizzes.values():
            options.append(item["name"])
        self.quizz_selector = create_Combobox(
            frame_inputs,
            values=options,
            state="readonly",
            row=0,
            column=0,
            sticky="n",
            width=50,
            columnspan=2,
        )
        self.quizz_selector.bind("<<ComboboxSelected>>", self.select_quiz)
        self.quizz_selector.set("Seleccione una encuesta")

        # employee making the quizz data
        self.names, self.emps_metadata = get_name_id_employees_list(1, True)
        create_label(
            frame_inputs, text="Empleado encuestado: ", row=1, column=0, sticky="w"
        )
        self.name_emp_selector = create_Combobox(
            frame_inputs,
            values=self.names,
            state="readonly",
            width=40,
            row=1,
            column=1,
            sticky="w",
        )
        # evaluated employee
        self.label_evaluated = create_label(frame_inputs, text="Empleado evaluado: ", row=0, column=2, sticky="w")
        self.label_evaluated.grid_remove()
        self.name_emp_evaluated = create_Combobox(
            frame_inputs, values=self.names, state="readonly", width=40,
            row=0, column=3, sticky="w"
        )
        self.name_emp_evaluated.grid_remove()
        self.label_pos_evaluator = create_label(frame_inputs, text="Nivel del evaluado: ", row=1, column=2, sticky="w")
        self.label_pos_evaluator.grid_remove()
        self.pos_evaluator = create_Combobox(
            frame_inputs, values=["Autoevaluación", "Jefe Inmediato", "Colega", "Subordinado"],
            state="readonly", width=40,
            row=1, column=3, sticky="w"
        )
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
            "date": datetime.now().strftime("%d/%m/%Y"),
            "interviewer": self.interviewer,
            "ID_emp": data_emp_questioned[1],
            "position": data_emp_questioned[2],
            "admision": data_emp_questioned[3],
            "departure": data_emp_questioned[4]["date"],
            "departure_reason": data_emp_questioned[4]["reason"],
            "evaluated_emp": self.name_emp_evaluated.get(),
            "pos_evaluator": self.pos_evaluator.get(),
            "evaluated_emp_ID": data_emp_evaluated[1],
        }
        name_quizz = self.quizz_selector.get()
        self.dict_quizz = json.load(open(self.filepath, encoding="utf-8"))
        self.quizz = QuizMaker(self.frame_encuesta, self.dict_quizz, title=name_quizz,
                               tipo_id=self.tipo_id, out_path=self.quizz_out_path,
                               metadata=metadata)
        self.quizz.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")


class QuizzResultPDF(ttk.Frame):
    def __init__(self, master, quizzes=quizzes_RRHH, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        # ----------Title-------------
        ttk.Label(
            self, text="Resultados de Encuestas", font=("Helvetica", 30, "bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
        # ----------variables-------------
        self.quizzes = quizzes
        self.quizz = None
        self.dict_quizz = None
        self.filepath = None
        # ----------widgets-------------
        options = []
        for item in self.quizzes.values():
            options.append(item["name"])
        self.quizz_selector = create_Combobox(
            self,
            values=options,
            state="readonly",
            row=1,
            column=0,
            sticky="n",
            width=50,
        )
