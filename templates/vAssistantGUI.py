# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 25/dic./2023  at 13:30 $'

import ttkbootstrap as ttk
from tkinter import END, filedialog
from ttkbootstrap.scrolled import ScrolledText

import tkinter as tk

import os

from templates.openAI_functions import get_response_chat_completion, get_response_assistant

BG_GRAY = "#ABB2B9"
BG_COLOR = "#17202A"
TEXT_COLOR = "#EAECEE"

FONT_CHAT = "Helvetica 10"
FONT_Title = "Helvetica 13 bold"


class AssistantGUI(ttk.Frame):
    def __init__(self, master=None, context=None, department=None, language="spanish", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        # self.grid(row=0, column=0)
        self.columnconfigure((0, 1), weight=1)
        self.rowconfigure(2, weight=1)
        #  -------------------create variables-----------------
        self.department = department if department is not None else "IT"
        self.language = language if language is not None else "spanish"
        self.context = [{"role": "system",
                        "content": f"Act as an Virtual Assistant, you work aiding in a telecomunications enterprise called Telintec. \n"
                                   f"You help in the {self.department} and you answer are concise and precise.\n"
                                   f"You answer in {self.language}."}
                        ] if context is None else context
        self.flag_context_init = True if context is not None else False
        self.files_AV = []
        #  -------------------create title-----------------
        lable1 = ttk.Label(self, text="Asistente Virtual", font=FONT_Title)
        lable1.grid(row=0, column=0, columnspan=2, sticky="n", padx=10, pady=10)
        #  -------------------create type selector checkbutton-----------------
        self.var_type_AV = tk.BooleanVar(value=False)
        self.var_type_text = tk.StringVar(value="Permitir Archivos")
        self.type_AV = ttk.Checkbutton(self,
                                       textvariable=self.var_type_text,
                                       variable=self.var_type_AV,
                                       command=self.change_type_AV,
                                       bootstyle="round-toggle")
        self.type_AV.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        #  -------------------create reset chat btn-----------------
        self.btn_reset = ttk.Button(self, text="Reset Chat", command=self.reset_chat)
        self.btn_reset.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        #   -------------------create message----------------
        self.txt = ttk.Text(self, width=15, state=tk.DISABLED)
        self.txt.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.txt.tag_config("user", foreground="blue")
        self.txt.delete(1.0, tk.END)
        #    -------------------create input----------------
        self.entry_msg = ttk.Entry(self, font=FONT_CHAT)
        self.entry_msg.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        send = ttk.Button(self, text="Send", command=self.send_txt)
        send.grid(row=4, column=0,  sticky="nsew", padx=5, pady=5)
        #  -------------------create file selector btn----------------
        self.btn_file = ttk.Button(self, text="Upload File",
                                   command=self.button_file_click)
        self.btn_file.grid(row=5, column=0, sticky="nsew", padx=5, pady=5)
        self.btn_file_erase = ttk.Button(self, text="Erase File",
                                         command=self.button_file_erase)
        self.btn_file_erase.grid(row=5, column=1, sticky="nsew", padx=5, pady=5)
        self.label_file = ttk.Label(self, text="Archivos subidos: ")
        self.label_file.grid(row=6, column=0, sticky="nsew", padx=5, pady=(5, 0))
        self.files_cb = ttk.Combobox(self, values=["no file selected"], state="readonly")
        self.files_cb.grid(row=7, column=0, sticky="nsew", padx=5, pady=5, columnspan=2)

    def send_txt(self):
        self.txt.configure(state="normal")
        if self.flag_context_init:
            for iteraction in self.context:
                if iteraction["role"] == "user":
                    self.txt.insert(END, "User: " + iteraction["content"] + "\n")
                elif iteraction["role"] == "assistant":
                    self.txt.insert(END, "AV: " + iteraction["content"] + "\n")
            self.flag_context_init = False
        msg = "User: " + self.entry_msg.get()
        self.txt.insert(END, msg + "\n")
        last_line = float(self.txt.index(END))-2.0
        self.txt.tag_add("user", last_line, f"{int(last_line)}.end+1c")
        response = self.get_response(self.entry_msg.get())
        self.txt.insert(END, "AV: " + response + "\n")
        self.update_context(self.entry_msg.get(), response)
        self.txt.configure(state=tk.DISABLED)
        self.txt.see(END)
        self.entry_msg.delete(0, END)

    def change_context(self, new_context):
        """
        This method change the context of the virtual assistant.

        :param new_context:
        """
        self.context = new_context

    def get_response(self, msg):
        # return "dummy answer, dummy answer"
        if self.var_type_AV.get():
            # files supported
            self.files_AV, res = get_response_assistant(msg, self.files_AV)
            print("Responge assistant gpt: ", res)
        else:
            # files not supported
            self.context.append({"role": "user", "content": msg})
            res = get_response_chat_completion(self.context)
            print("Responge gpt: ", res)
        return res

    def update_context(self, msg, response):
        self.context.append({"role": "user", "content": msg})
        self.context.append({"role": "assistant", "content": response})

    def change_type_AV(self):
        if self.var_type_AV.get():
            self.var_type_text.set("Permitir Archivos")
            self.btn_file.configure(state="normal")
            self.btn_file_erase.configure(state="normal")
            self.files_cb.configure(state="readonly")
            self.label_file.configure(text="Archivos subidos: ")
        else:
            self.var_type_text.set("No Permitir Archivos")
            self.btn_file.configure(state="disabled")
            self.btn_file_erase.configure(state="disabled")
            self.files_cb.configure(state="disabled")
            self.label_file.configure(text="")

    def reset_chat(self):
        self.txt.configure(state="normal")
        self.txt.delete(1.0, tk.END)
        self.txt.configure(state=tk.DISABLED)
        self.context = [{"role": "system",
                        "content": f"Act as an Virtual Assistant, you work aiding in a telecomunications enterprise called Telintec. \n"
                                   f"You help in the {self.department}"}
                        ]

    def button_file_click(self):
        # select filepath
        filepath = filedialog.askopenfilename(initialdir="/", title="Select file",
                                              filetypes=(("text files", "*.txt"), ("all files", "*.*")))
        self.files_AV.append(
            {"path": filepath,
             "name": os.path.basename(filepath),
             "file_openai": None}
        )
        files_names = [item["name"] for item in self.files_AV]
        self.files_cb.configure(values=files_names)
        self.files_cb.set(files_names[0])
        # display filepath
        print(filepath)

    def button_file_erase(self):
        if self.files_cb.get() != "no file selected" and len(self.files_AV) > 0:
            for item in self.files_AV:
                if item["name"] == self.files_cb.get():
                    self.files_AV.remove(item)
                    print(f"file erased: {item['name']}")
        files_names = [item["name"] for item in self.files_AV]
        files_names = ["no file selected"] if len(files_names) == 0 else files_names
        self.files_cb.configure(values=files_names)
        self.files_cb.set(files_names[0])


if __name__ == '__main__':
    root = ttk.Window()
    root.title('vAssistant')
    root.geometry('250x500')
    app = AssistantGUI(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
