# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 13/feb./2024  at 15:36 $'

import json
from tkinter import IntVar

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from static.extensions import quizzes_RRHH
from templates.Funtions_Utils import create_Combobox
from templates.PDFGenerator import create_pdf_quizz_salida


class QuizMaker(ttk.Frame):
    def __init__(self, master, dict_quizz, title=None):
        super().__init__(master)
        self.q_no = 0
        self.title = title if title is not None else "Quiz"
        self.dict_quizz = dict_quizz
        self.questions_label = None
        self.opt_selected = []
        self.data_size = len(self.dict_quizz)
        self.correct = 0
        # ----------widgets-------------
        self.columnconfigure(0, weight=1)
        self.frame_questions = ttk.Frame(self)
        self.frame_questions.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_questions.columnconfigure(0, weight=1)
        self.frame_options = ttk.Frame(self)
        self.frame_options.grid(row=2, column=0, padx=20, pady=10, sticky="n")
        self.frame_buttons = ttk.Frame(self)
        self.frame_buttons.grid(row=3, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_buttons.columnconfigure((0, 1), weight=1)
        self.display_title()
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
        self.frame_options = ttk.Frame(self)
        self.frame_options.grid(row=2, column=0, padx=10, pady=10, sticky="n")

    def display_title(self):
        title = ttk.Label(self, text=self.title, width=50, font=("ariel", 20, "bold"))
        title.grid(row=0, column=0, padx=10, pady=10)

    def display_result(self):
        Messagebox.show_info(
            title="Result",
            message=f"Your answers are: {self.opt_selected}\n"
        )

    def next_btn(self):
        self.save_result()
        self.q_no += 1
        if self.q_no == self.data_size:
            self.display_result()
            self.master.update_dict_quizz(self.dict_quizz)
            self.destroy()
        else:
            self.recreate_frames()
            self.display_question()
            self.entries = self.display_options()

    def buttons(self):
        next_btn = ttk.Button(
            self.frame_buttons, text="Next", command=self.next_btn,
            width=10, bootstyle="primary")
        next_btn.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    def display_question(self):
        if self.questions_label is not None:
            self.questions_label.destroy()
        self.questions_label = ttk.Label(
            self.frame_questions,
            text=self.dict_quizz[str(self.q_no)]["question"],
            font=('ariel', 12, 'bold'), anchor="n")
        colunmspan = 1
        if self.dict_quizz[str(self.q_no)]["type"] == 3:
            colunmspan = len(self.dict_quizz[str(self.q_no)]["options"]) + 1
        self.questions_label.grid(row=0, column=0, columnspan=colunmspan,
                                  padx=10, pady=10, sticky="nswe")

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
                    ttk.Checkbutton(self.frame_options, text=item, onvalue=1, offvalue=0,
                                    variable=var).grid(
                        row=index_y + 1, column=index_x, sticky="w", padx=10, pady=10)
                    q_list.append(var)
            case 2:
                options = self.dict_quizz[str(self.q_no)]["options"]
                q_list.append(IntVar())
                for index, item in enumerate(options):
                    ttk.Radiobutton(self.frame_options, text=item,
                                    variable=q_list[-1], value=index).grid(
                        row=index + 1, column=0, sticky="w", padx=5, pady=5)
            case 3:
                options = self.dict_quizz[str(self.q_no)]["options"]
                subquetions = self.dict_quizz[str(self.q_no)]["subquestions"]
                for index_x, item in enumerate(options):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=1, column=index_x + 1, sticky="n", padx=10, pady=3)
                for index_y, item in enumerate(subquetions):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=index_y + 2, column=0, sticky="w", pady=3)
                    q_list.append(IntVar())
                    for index_x, subitem in enumerate(options):
                        ttk.Radiobutton(self.frame_options, text="",
                                        variable=q_list[-1], value=index_x).grid(
                            row=index_y + 2, column=index_x + 1, sticky="n", pady=3)
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

            case _:
                self.opt_selected.append(self.entries[0].get("1.0", "end-1c"))
        self.dict_quizz[str(self.q_no)]["answer"] = self.opt_selected[-1]


class FrameEncuestas(ttk.Frame):
    def __init__(self, master, quizzes=quizzes_RRHH, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        # ----------Title-------------
        ttk.Label(self, text="Encuestas",
                  font=("Helvetica", 30, "bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="nswe")
        # ----------variables-------------
        self.quizzes = quizzes
        self.quizz = None
        self.dict_quizz = None
        self.filepath = None
        # ----------widgets-------------
        options = []
        for item in self.quizzes.values():
            options.append(item["name"])
        self.quizz_selector = create_Combobox(self, values=options, state="readonly",
                                              row=1, column=0, sticky="n", width=50)
        self.quizz_selector.bind("<<ComboboxSelected>>", self.select_quiz)
        self.quizz_selector.set("Seleccione una encuesta")
        ttk.Button(self, text="Crear Encuesta", command=self.create_quiz,
                   width=20, bootstyle="primary").grid(
            row=1, column=1, padx=10, pady=10, sticky="n")

    def select_quiz(self, event=None):
        quiz_name = event.widget.get()
        flag = False
        for item in self.quizzes.values():
            if item["name"] == quiz_name:
                self.filepath = item["path"]
                flag = True
                self.dict_quizz = json.load(open(self.filepath, encoding="utf-8"))
                break
        if not flag:
            self.filepath = None
            self.dict_quizz = None
            self.quizz = None

    def create_quiz(self):
        if self.dict_quizz is None:
            return
        print("creating quizz")
        name = self.quizz_selector.get()
        self.dict_quizz = json.load(open(self.filepath, encoding="utf-8"))
        self.quizz = QuizMaker(self, self.dict_quizz, title=name)
        self.quizz.grid(row=2, column=0, padx=10, pady=10, sticky="nswe")

    def update_dict_quizz(self, new_dict: dict):
        self.dict_quizz = new_dict
        name_emp = "employee 1"
        job = "position 1"
        terminal = "terminal"
        date_start = "01/01/2021"
        date_end = "31/12/2021"
        date_inteview = "01/01/2021"
        name_interviewer = "Interviewer"
        file_out = f"C:/Users/Edisson/Documents/sample.pdf"
        create_pdf_quizz_salida(self.dict_quizz, None, file_out,
                                name_emp, job, terminal, date_start, date_end, date_inteview,
                                name_interviewer)
        print(f"quizz update and pdf generated at {file_out}")


class QuizzResultPDF(ttk.Frame):
    def __init__(self, master, quizzes=quizzes_RRHH, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        # ----------Title-------------
        ttk.Label(self, text="Resultados de Encuestas",
                  font=("Helvetica", 30, "bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="nswe")
        # ----------variables-------------
        self.quizzes = quizzes
        self.quizz = None
        self.dict_quizz = None
        self.filepath = None
        # ----------widgets-------------
        options = []
        for item in self.quizzes.values():
            options.append(item["name"])
        self.quizz_selector = create_Combobox(self, values=options, state="readonly",
                                              row=1, column=0, sticky="n", width=50)