# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 09/nov./2023  at 14:41 $'

import tkinter as tk

import ttkbootstrap as ttk
import unicodedata

from templates import GUIGeneral
from templates.ExamenesMedicos import ExamenesMedicosFrame
from templates.vAssistantGUI import AssistantGUI


def clean_accents(txt: str):
    return unicodedata.normalize('NFKD',txt).encode('ASCII', 'ignore').decode('ASCII')


if __name__ == '__main__':
    # cb.save_directory_index(paths_dpb_folders, online=False, father=local_father_path_dpb)
    # directories = cb.load_directory_file(paths_dpb_folders, local=True)
    # for directory in directories:
    #     print(directory)
    # directories = cb.load_directory_file(paths_dpb_folders, local=False)
    # for directory in directories:
    #     print(directory)
    # read excel
    # skip_rows = [0, 1, 2]
    # rows = [i for i in range(3142) if i not in skip_rows]
    # cols = [0, 1, 2]
    # df = pd.read_excel('files/Ternium_13-11-2023.xls', skiprows=skip_rows, usecols=cols)
    # df.dropna(inplace=True)
    # df["Fecha/hora"] = cb.clean_date(df["Fecha/hora"].tolist())
    # df.dropna(subset=['Fecha/hora'], inplace=True)
    # df["Fecha/hora"] = pd.to_datetime(df["Fecha/hora"], format="mixed", dayfirst=True)
    # df["status"], df["name"], df["card"], df["in_out"] = cb.clean_text(df["Texto"].to_list())
    # df_name = df[df["name"] == "RIVERA B, ALFREDO"]
    # limit_hour = pd.Timestamp(f"{8}:{30}:00")
    # count = len(df_name[df_name["Fecha/hora"].dt.time > limit_hour.time()])
    # print(count)
    # lates = df_name[df_name["Fecha/hora"].dt.time > limit_hour.time()]
    # for i in lates["Fecha/hora"]:
    #     time_str = str(i)
    #     time_str = time_str.split(" ")[1]
    #     time_str = pd.Timestamp(time_str)
    #     print(time_str)
    #     print(limit_hour)
    #     diff = time_str - limit_hour
    #     print(diff.seconds/60)

    # # read excel
    # filename = 'files/OCTreport_31-10-2023.xlsx'
    # excel_file = pd.ExcelFile(filename)
    # sheet_names = excel_file.sheet_names
    # inital_skip_rows = 9
    # contracts = {}
    # for sheet in sheet_names:
    #     if sheet == "VEHICULOS":
    #         continue
    #     skip_rows = [i for i in range(0, 9)]
    #     # skip_rows = [i for i in range(9)] + [i for i in range(13, 3142)]
    #     rows = [i for i in range(3142) if i not in skip_rows]
    #     cols = [0, 1, 2]
    #     df = pd.read_excel(excel_file, skiprows=skip_rows, sheet_name=sheet)
    #     df.to_csv('files/OCT_report_1.csv')
    #     data = []
    #     with open('files/OCT_report_1.csv', mode="r", encoding='utf-8') as csv_file:  # "r" represents the read mode
    #         reader = csv.reader(csv_file)  # this is the reader object
    #         for item in reader:
    #             data.append(item)
    #     employees = {}
    #     indexes = range(len(data))
    #     starting_indexes = [indexes[i] for i in range(0, len(indexes), 4)]
    #     data_sliced = [data[i:i + 4] for i in starting_indexes]
    #     for data_aux in data_sliced:
    #         status = []
    #         fechas = []
    #         comments = []
    #         extras = []
    #         primas = []
    #         in_door = []
    #         out_door = []
    #         for i in range(len(data_aux)):
    #             if i == 1:
    #                 name = clean_accents(data_aux[i][1])
    #                 for j in range(2, len(data_aux[i])):
    #                     if j % 2 != 1:
    #                         in_door.append(data_aux[i][j])
    #                     else:
    #                         out_door.append(data_aux[i][j])
    #             elif i == 0:
    #                 for j in range(2, len(data_aux[i])):
    #                     if j % 2 != 1:
    #                         fechas.append(data_aux[i][j])
    #                     else:
    #                         status.append(data_aux[i][j])
    #             elif i == 2:
    #                 for j in range(2, len(data_aux[i])):
    #                     if j % 2 != 1:
    #                         comments.append(data_aux[i][j])
    #             elif i == 3:
    #                 for j in range(2, len(data_aux[i])):
    #                     if j % 2 != 1:
    #                         extras.append(data_aux[i][j])
    #                     else:
    #                         primas.append(data_aux[i][j])
    #         if name != "":
    #             employees[name] = {
    #                 "fechas": fechas,
    #                 "status": status,
    #                 "comments": comments,
    #                 "extras": extras,
    #                 "primas": primas,
    #                 "in_door": in_door,
    #                 "out_door": out_door,
    #             }
    #     contracts[sheet] = employees
    # print(contracts["ALMACEN"].keys())
    # format(convert_date(45200.0), '%m/%d/%Y')
    # for i in range(4):
    #     data[i][:] = convert_date(data[i][0])
    # app = ttk.Window(themename='vapor')
    # app.title("Fichajes Files GUI")
    # app.after(0, lambda: app.state('zoomed'))
    # app.columnconfigure(0, weight=1)
    # main = FichajesFilesGUI(app)
    # main.pack(fill='both', expand=True)
    # app.mainloop()
    main = GUIGeneral.GUIAsistente(themename='vapor')
    main.mainloop()
    # root = ttk.Window()
    # root.title('vAssistant')
    # root.geometry('250x500')
    # app = AssistantGUI(root, department="RRHH")
    # # app = ExamenesMedicosFrame(root)
    # app.pack(fill=tk.BOTH, expand=True)
    # root.mainloop()
