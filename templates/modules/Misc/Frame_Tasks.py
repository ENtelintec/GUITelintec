# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 24/may./2024  at 16:13 $'

import json

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from static.extensions import quizzes_dir_path, filepath_settings
from templates.Functions_Utils import create_label, create_button
from templates.controllers.misc.tasks_controller import get_all_tasks_by_status, update_task
from templates.modules.RRHH.SubFrame_QuizzMaker import QuizMaker

avaliable_tasks = {
    "quizz": QuizMaker
}

dict_status = {0: "Pendiente", 1: "Compleatado"}


def check_status(item):
    if item[2] == dict_status[1]:
        return True
    else:
        return False


def create_rowdata_tasks(tasks):
    coldata = []
    for task in tasks:
        id_task = task[0]
        body = json.loads(task[1])
        coldata.append([id_task, body["title"], dict_status[body["status"]], json.dumps(body)])
    return coldata


def create_kwargs(name, body: dict, id_task):
    match name:
        case "quizz":
            settings = json.load(open(filepath_settings, encoding="utf-8"))
            quizzes_dir = json.load(open(quizzes_dir_path, encoding="utf-8"))
            dict_quizz = json.load(open(quizzes_dir[str(body["metadata"]["type_quizz"])]["path"], encoding="utf-8"))
            title = quizzes_dir[str(body["metadata"]["type_quizz"])]["name"]
            tipe_id = body["metadata"]["type_quizz"]
            path_out = settings["gui"]["RRHH"]["files_quizz_out"]
            metadata = body["metadata"]
            return {
                "dict_quizz": dict_quizz,
                "title": title,
                "tipo_id": tipe_id,
                "out_path": path_out,
                "metadata": metadata,
                "id_task": id_task
            }
        case _:
            return {"metadata": body["metadata"]}


class FrameTasks(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        # ----------------------------------Title-------------------------------
        create_label(self, 0, 0, text='Tasks', font=('Helvetica', 18))
        # --------------------------------Variables-----------------------------
        self.task_selector = None
        self.rowdata = None
        self.id_task = None
        self._is_task_complete = True
        self.username_data = kwargs.get("username_data")
        self.id_emp = self.username_data["id"]
        flag, error, self.tasks = get_all_tasks_by_status(status=-1, id_destiny=self.id_emp) if "tasks" not in kwargs["data"] else (True, "", kwargs["data"]["tasks"]["data"])
        # --------------------------------selector task-------------------------
        self.frame_selector = ttk.Frame(self)
        self.frame_selector.grid(row=1, column=0, sticky='nsew')
        self.frame_selector.columnconfigure(0, weight=1)
        self.task_selector = self.create_table_tasks(self.frame_selector)
        # ---------------------------buttons-----------------------------------
        frame_btns = ttk.Frame(self)
        frame_btns.grid(row=2, column=0, sticky='nsew')
        frame_btns.columnconfigure(0, weight=1)
        create_button(frame_btns, 0, 0, text="Actualizar tareas", command=self.update_table, width=20, sticky="n")

    def create_table_tasks(self, master):
        columns = ["ID", "Titulo", "Estado", "Body"]
        coldata = []
        for column in columns:
            if "Estado" in column:
                coldata.append({"text": column, "stretch": False, "width": 150})
            elif "Estado" in column:
                coldata.append({"text": column, "stretch": False, "width": 85})
            else:
                coldata.append({"text": column, "stretch": True})
        self.rowdata = create_rowdata_tasks(self.tasks)
        table_notifications = Tableview(master, 
                                        coldata=coldata, 
                                        autofit=False, 
                                        paginated=False,
                                        searchable=False,
                                        rowdata=self.rowdata,
                                        height=15)
        table_notifications.grid(row=1, column=0, sticky="nswe", padx=(5, 30))
        table_notifications.view.tag_configure("complete", font=("Arial", 10, "normal"), background="white")
        table_notifications.view.tag_configure("incomplete", font=("Arial", 11, "bold"), background="#98F5FF")
        items_t = table_notifications.view.get_children()
        for item_t in items_t:
            if check_status(table_notifications.view.item(item_t, "values")):
                table_notifications.view.item(item_t, tags="complete")
            else:
                table_notifications.view.item(item_t, tags="incomplete")
        table_notifications.view.bind("<Double-1>", self._on_double_click_table)
        columns_header = table_notifications.get_columns()
        for item in columns_header:
            if item.headertext in ["ID", "Body"]:
                item.hide()
        return table_notifications

    def _on_double_click_table(self, event): 
        if not self._is_task_complete:
            print(f"La tarea con ID: {str(self.id_task)} no se ha completado aun")
        self._is_task_complete = False
        item = event.widget.item(event.widget.selection()[0], "values")
        self.id_task = int(item[0])
        body = json.loads(item[3])
        if body["title"] in avaliable_tasks:
            kwargs = create_kwargs(body["title"], body, self.id_task)
            avaliable_tasks[body["title"]](master=self, **kwargs)
        else:
            print("No se encontro el tipo de tarea")
    
    def end_task(self, data_out):
        self._is_task_complete = True
        for index, item in enumerate(self.tasks):
            if item[0] == data_out["id"]:
                body = json.loads(item[1])
                body["status"] = 1
                body["path_out"] = data_out["path_out"]
                flag, error, out = update_task(data_out["id"], body, 1)
                if not flag:
                    print(str(error))
                else:
                    print(f"La tarea con ID: {data_out['id']} se ha completado")
                    row = (self.id_task, json.dumps(body))
                    self.tasks[index] = row
                break
        
        self.update_table()

    def update_table(self):
        self.task_selector.destroy() if self.task_selector is not None else None
        self.task_selector = self.create_table_tasks(self.frame_selector)
