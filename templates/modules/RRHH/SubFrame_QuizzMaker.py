# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 13/may./2024  at 15:20 $'

from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

from static.extensions import quizz_out_path, format_timestamps_filename
from templates.misc.Functions_AuxFiles import save_json_file_quizz
from templates.Functions_GUI_Utils import calculate_results_quizzes, recommendations_results_quizzes
from templates.PDFGenerator import create_pdf_quizz_salida, create_pdf__quizz_nor035_v1, \
    create_pdf_quizz_nor035_50_plus, create_quizz_clima_laboral, create_quizz_eva_360  


class QuizMaker(ttk.Toplevel):
    def __init__(self, dict_quizz, title=None, tipo_id=0, out_path=quizz_out_path, 
                 metadata: dict = None, master=None, **kwargs):
        super().__init__(master)
        self.master = master
        self.title(title)
        self.state("zoomed")
        self.quizz_out_path = out_path
        self.q_no = 0
        self.title_str = title if title is not None else "Quiz"
        self.dict_quizz = dict_quizz
        self.id_task = kwargs.get("id_task")
        self.metadata = metadata
        print(self.metadata)
        self.questions_label = None
        self.opt_selected = []
        self.data_size = len(self.dict_quizz)
        self.correct = 0
        self.tipo_quizz = tipo_id
        self.last_default = False
        self.questions_default = []
        # ----------widgets-------------
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.display_title()
        self.frame_questions = ttk.Frame(self)
        self.frame_questions.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        self.frame_questions.columnconfigure(0, weight=1)
        self.frame_questions.rowconfigure(1, weight=1)
        self.scroll_questions_frame = ScrolledFrame(self, autohide=True)
        self.scroll_questions_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nswe")
        self.scroll_questions_frame.columnconfigure(0, weight=1)
        self.scroll_questions_frame.rowconfigure(0, weight=1)
        self.frame_options = ttk.Frame(self.scroll_questions_frame)
        self.frame_options.grid(row=0, column=0, padx=20, pady=10, sticky="nswe")
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
        self.frame_options = ttk.Frame(self.scroll_questions_frame)
        self.frame_options.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")

    def display_title(self):
        title = ttk.Label(self, text=self.title_str, font=("ariel", 20, "bold"))
        title.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    def display_result(self):
        dict_results = calculate_results_quizzes(self.dict_quizz, self.tipo_quizz)

        Messagebox.show_info(
            title="Result",
            message=f"Your final result is:\n"
                    f"Calificación final: {dict_results['c_final']}\n"
                    f"Calificación de dominio: {dict_results['c_dom']}\n"
                    f"Calificacion de categoria: {dict_results['c_cat']}\n"
                    f"----RECOMENDACIONES----",
        )
        return dict_results

    def display_recommendations(self):
        dict_recommendations = recommendations_results_quizzes(
            self.dict_quizz, self.tipo_quizz
        )
        Messagebox.show_info(
            title="Recommendations",
            message=f"Algunas recomendaciones : \n"
                    f"Se recomienda Para la calificacion final{dict_recommendations['c_final_r']}\n"
                    f"Se recomienda Para la calificacion de dominio{dict_recommendations['c_dom_r']}\n"
                    f"Se recomienda Para la calificacion categoria{dict_recommendations['c_cat_r']}\n",
        )
        return dict_recommendations

    def next_btn(self):
        self.save_result()
        self.q_no += 1
        if self.q_no == self.data_size:
            dict_results = self.display_result()
            dict_recommendations = self.display_recommendations()
            self.update_dict_quizz(
                self.dict_quizz,
                tipo_op=self.tipo_quizz,
                dict_results=dict_results,
                dict_recommendations=dict_recommendations,
            )
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
                index_cols = []
                index_rows = []
                cols = 1
                options = self.dict_quizz[str(self.q_no)]["options"]
                if len(options) > 4:
                    cols = 3
                for index, item in enumerate(options):
                    var = ttk.IntVar()
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
                    index_cols.append(index_x)
                    index_rows.append(index_y+1)
                    q_list.append(var)
                self.frame_options.columnconfigure(index_cols, weight=1)
                self.frame_options.rowconfigure(index_rows, weight=1)
            case 2:
                index_rows = []
                options = self.dict_quizz[str(self.q_no)]["options"]
                q_list.append(ttk.IntVar())
                for index, item in enumerate(options):
                    ttk.Radiobutton(
                        self.frame_options, text=item, variable=q_list[-1], value=index
                    ).grid(row=index + 1, column=0, sticky="w", padx=5, pady=5)
                    index_rows.append(index + 1)
                self.frame_options.columnconfigure(0, weight=1)
                self.frame_options.rowconfigure(index_rows, weight=1)
            case 3:
                indexes_cols = []
                indexes_rows = []
                options = self.dict_quizz[str(self.q_no)]["options"]
                subquetions = self.dict_quizz[str(self.q_no)]["subquestions"]
                for index_x, item in enumerate(options):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=1, column=index_x + 1, sticky="n", padx=10, pady=3
                    )
                    indexes_cols.append(index_x)
                    indexes_rows.append(1)
                for index_y, item in enumerate(subquetions):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=index_y + 2, column=0, sticky="w", pady=3
                    )
                    indexes_rows.append(index_y + 2)
                    q_list.append(ttk.IntVar())
                    index_x = 0
                    for index_x, subitem in enumerate(options):
                        ttk.Radiobutton(
                            self.frame_options,
                            text="",
                            variable=q_list[-1],
                            value=index_x,
                        ).grid(row=index_y + 2, column=index_x + 1, sticky="n", pady=3)
                        if index_x + 1 not in indexes_cols:
                            indexes_cols.append(index_x + 1)
                    if index_y + 2 not in indexes_rows:
                        indexes_rows.append(index_y + 2)
                    if self.last_default and self.q_no in self.questions_default:
                        q_list[-1].set(index_x)
                self.frame_options.columnconfigure(indexes_cols, weight=1)
                self.frame_options.rowconfigure(indexes_rows, weight=1)
            case 4:
                indexes_cols = []
                indexes_rows = []
                options = self.dict_quizz[str(self.q_no)]["options"]
                subquetions = self.dict_quizz[str(self.q_no)]["subquestions"]
                for index_x, item in enumerate(options):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=1, column=index_x + 1, sticky="n", padx=10, pady=3
                    )
                    indexes_cols.append(index_x)
                    indexes_rows.append(1)
                for index_y, item in enumerate(subquetions):
                    ttk.Label(self.frame_options, text=item).grid(
                        row=index_y + 2, column=0, sticky="w", pady=3
                    )
                    q_list.append(ttk.IntVar())
                    for index_x, subitem in enumerate(options):
                        ttk.Radiobutton(
                            self.frame_options,
                            text="",
                            variable=q_list[-1],
                            value=index_x,
                        ).grid(row=index_y + 2, column=index_x + 1, sticky="n", pady=3)
                        if index_x + 1 not in indexes_cols:
                            indexes_cols.append(index_x + 1)
                    if index_y + 2 not in indexes_rows:
                        indexes_rows.append(index_y + 2)
                self.frame_options.columnconfigure(indexes_cols, weight=1)
                self.frame_options.rowconfigure(indexes_rows, weight=1)
            case _:
                txt_entry = ttk.Text(self.frame_options, height=10, font=("ariel", 14))
                txt_entry.grid(row=1, column=0, sticky="nswe", padx=10, pady=10)
                q_list.append(txt_entry)
                self.frame_options.columnconfigure(0, weight=1)
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

    def update_dict_quizz(
            self, new_dict: dict, tipo_op, dict_results, dict_recommendations
    ):

        self.dict_quizz = new_dict
        self.dict_quizz["results"] = dict_results
        self.dict_quizz["recommendations"] = dict_recommendations
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
        elif tipo_op == 1:
            create_pdf__quizz_nor035_v1(
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
        elif tipo_op == 2:
            create_pdf_quizz_nor035_50_plus(
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
        result_name = (
            f"Quiz_{tipo_op}_{id_emp}_{datetime.now().strftime(format_timestamps_filename)}.json"
        )
        self.metadata["date"] = str(self.metadata["date"])
        self.metadata["admision"] = str(self.metadata["admision"])
        self.metadata["type_q"] = tipo_op
        self.metadata["title"] = self.title_str
        self.dict_quizz["metadata"] = self.metadata
        save_json_file_quizz(self.dict_quizz, quizz_out_path + result_name)
        data_out = {
            "id":  self.id_task,
            "path_out": quizz_out_path + result_name,
            "metadata": self.metadata,
        }
        self.master.end_task(data_out)

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
