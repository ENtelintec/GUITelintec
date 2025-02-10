# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 30/jul./2024  at 13:01 $"

import json
from datetime import datetime
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.tableview import Tableview

from static.constants import filepath_daemons
from templates.Functions_GUI_Utils import (
    create_label,
    create_Combobox,
    create_button,
    create_entry,
)
from templates.Functions_Sharepoint import (
    create_mail_draft_with_attachment,
    download_files_site,
)
from templates.controllers.employees.employees_controller import get_emp_mail
from templates.controllers.payroll.payroll_controller import (
    update_payroll,
    update_payroll_employees,
    get_payrolls_with_info,
)
from templates.daemons.Files_handling import UpdaterSharepointNomina
from templates.misc.Functions_AuxFiles import get_data_xml_file_nomina


def transform_number_month_to_String(months: list):
    months_string_dict = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    months_string = [months_string_dict[int(month)] for month in months]
    return months_string


def transform_string_month_to_int(months: list):
    months_int_dict = {
        "Enero": 1,
        "Febrero": 2,
        "Marzo": 3,
        "Abril": 4,
        "Mayo": 5,
        "Junio": 6,
        "Julio": 7,
        "Agosto": 8,
        "Septiembre": 9,
        "Octubre": 10,
        "Noviembre": 11,
        "Diciembre": 12,
    }
    months_int = [months_int_dict[month] for month in months]
    return months_int


class PayrollFilesGUI(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.data_file_emp = None
        self.columnconfigure(0, weight=1)
        self.payrolls_info = kwargs["data"]["nominas"]
        self.selected_file = None
        self._svar_txt_sent = ttk.StringVar(value="")
        self._svar_txt_date = ttk.StringVar(value="")
        self._svar_txt_data_pay = ttk.StringVar(value="")
        self.user_data = kwargs["username_data"]
        create_label(
            self, text="Documentos de Nomina", row=0, column=0, font=("Arial", 18)
        )

        frame_1 = ttk.Frame(self)
        frame_1.grid(row=1, column=0, sticky="nswe")
        frame_1.columnconfigure((0, 1, 2), weight=1)
        self.entries = self.create_inputs(frame_1)
        frame_2 = ttk.Frame(self)
        frame_2.grid(row=2, column=0, sticky="nswe")
        frame_2.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.create_buttons(frame_2)
        self.frame_3 = ttk.Frame(self)
        self.frame_3.grid(row=3, column=0, sticky="nswe", padx=(5, 20))
        self.frame_3.columnconfigure(0, weight=1)
        self.table_display = self.create_table_display()

    def create_inputs(self, master):
        emps_names = [
            emp[1].upper() + " " + emp[2].upper()
            for emp in self.payrolls_info["payrolls"]
        ]
        emps_names.sort()
        create_label(master, text="Empleado", row=0, column=0)
        name_emp_selector = create_Combobox(master, values=emps_names, row=0, column=1)

        create_label(master, text="Año", row=1, column=0)
        year = create_Combobox(master, values=["No data"], row=1, column=1)
        year.bind("<<ComboboxSelected>>", self.update_months)

        create_label(master, text="Mes", row=2, column=0)
        month = create_Combobox(master, values=["No data"], row=2, column=1)
        month.bind("<<ComboboxSelected>>", self.update_files)

        create_label(master, text="Archivos", row=3, column=0)
        filename = create_Combobox(master, values=["No data"], row=3, column=1)
        filename.bind("<<ComboboxSelected>>", self.update_selected_file)

        create_label(master, textvariable=self._svar_txt_sent, row=3, column=2)
        create_label(master, textvariable=self._svar_txt_date, row=2, column=2)
        create_label(master, textvariable=self._svar_txt_data_pay, row=1, column=2)
        return [name_emp_selector, year, month, filename, self._svar_txt_sent]

    def create_buttons(self, master):
        create_button(
            master,
            text="Actualizar archivos",
            row=0,
            column=0,
            command=self.refresh_data,
        )
        create_button(
            master, text="Crear Correo", row=0, column=1, command=self.create_email
        )
        create_button(
            master,
            text="Descargar archivos",
            row=0,
            column=2,
            command=self.create_files,
        )
        create_button(
            master,
            text="Actualizar Empleados",
            row=0,
            column=3,
            command=self.update_employees,
        )
        create_button(
            master,
            text="Actualizar Tabla",
            row=0,
            column=4,
            command=self.update_data_table,
        )

    def create_table_display(self):
        master = self.frame_3
        columns = self.payrolls_info["columns_payroll"]
        coldata = []
        for column in columns:
            if "Datos" in column:
                coldata.append({"text": column, "stretch": False, "width": 350})
            elif "Id" in column:
                coldata.append({"text": column, "stretch": False, "width": 30})
            elif "Nombre" in column:
                coldata.append({"text": column, "stretch": False, "width": 140})
            elif "Apellido" in column:
                coldata.append({"text": column, "stretch": False, "width": 140})
            else:
                coldata.append({"text": column, "stretch": True})
        data = self.payrolls_info["payrolls"]
        table = Tableview(
            master,
            bootstyle="primary",
            coldata=coldata,
            rowdata=data,
            paginated=False,
            searchable=True,
            autofit=False,
        )
        table.grid(row=1, column=0, sticky="nswe")
        table.view.bind("<Double-1>", self._on_double_click_table)
        columns_header = table.get_columns()
        for item in columns_header:
            if item.headertext in ["timestamp"]:
                item.hide()
        return table

    def _on_double_click_table(self, event):
        self.selected_file = None
        item = event.widget.selection()[0]
        # column = event.widget.identify_column(event.x)
        # col_index = int(column[1:])-1
        item_data = event.widget.item(item, "values")
        name = item_data[1] + " " + item_data[2]
        self.entries[0].set(name)
        self.id_emp_edit = int(item_data[0])
        self.data_emp_dict = json.loads(item_data[3])
        years = list(self.data_emp_dict.keys())
        years.sort(reverse=True)
        years = ["No data"] if len(years) == 0 else years
        self.entries[1].configure(values=years)

    def refresh_data(self):
        flags_daemons = json.load(open(filepath_daemons, "r"))
        if flags_daemons["update_files_nomina"]:
            msg = "Accion no permitida mientras se actualizan los datos."
            Messagebox.show_error(title="Error", message=msg)
            return
        EditPatternsUpdateDataPayroll(self)

    def update_data_action(self, patterns=None):
        thread_update = UpdaterSharepointNomina(patterns)
        thread_update.start()
        msg = "Datos actualizandose.\n Esto podria tardar varios minutos."
        flags_daemons = json.load(open(filepath_daemons, "r"))
        flags_daemons["update_files_nomina"] = True
        json.dump(flags_daemons, open(filepath_daemons, "w"))
        Messagebox.show_info(title="Info", message=msg)

    def create_email(self):
        flags_daemons = json.load(open(filepath_daemons, "r"))
        if flags_daemons["update_files_nomina"]:
            msg = "Accion no permitida mientras se actualizan los datos."
            Messagebox.show_error(title="Error", message=msg)
            return
        if self.selected_file is None:
            return
        email = self.user_data["email"]
        email_teli = email.split(",")[-1]
        if "telintec.com.mx" in email_teli.lower():
            MailCreation(self, email_source=email_teli, emp_destiny_id=self.id_emp_edit)
        else:
            MailCreation(self, emp_destiny_id=self.id_emp_edit)

    def create_draft(self, destiny_mail, subject, body, source_email):
        settings = json.load(open("files/settings.json", "r"))
        url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
        folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
        download_path_xml, code = download_files_site(
            url_shrpt + folder_rrhh, self.data_file_emp["xml"]
        )
        download_path_pdf, code = download_files_site(
            url_shrpt + folder_rrhh, self.data_file_emp["pdf"]
        )
        temp_files = [download_path_xml, download_path_pdf]
        response, code = create_mail_draft_with_attachment(
            self.id_emp_edit,
            source_email,
            subject,
            body,
            temp_files,
            to_recipients=destiny_mail,
        )
        if code == 200:
            msg = f"Correo creado correctamente para emp: {self.id_emp_edit}"
            Messagebox.show_info(title="Correo Creado", message=msg)
        else:
            Messagebox.show_error(title="Error", message=response)
            print(response)
        month = self.entries[2].get()
        month = transform_string_month_to_int([month])[0]
        self.data_emp_dict[self.entries[1].get()][str(month)][self.selected_file][
            "is_send"
        ] = 1
        flag, error, result = update_payroll(self.data_emp_dict, self.id_emp_edit)
        if flag:
            msg = (
                f"Base de datos actualizada correctamente para emp: {self.id_emp_edit}"
            )
            Messagebox.show_info(title="Correo Creado", message=msg)
        else:
            Messagebox.show_error(title="Error al actualizar DB", message=error)

    def create_files(self):
        flags_daemons = json.load(open(filepath_daemons, "r"))
        if flags_daemons["update_files_nomina"]:
            msg = "Accion no permitida mientras se actualizan los datos."
            Messagebox.show_error(title="Error", message=msg)
            return
        if self.selected_file is None:
            return
        file = self.selected_file
        month = self.entries[2].get()
        month = transform_string_month_to_int([month])[0]
        xml = pdf = None
        try:
            xml = self.data_emp_dict[self.entries[1].get()][str(month)][file]["xml"]
            pdf = self.data_emp_dict[self.entries[1].get()][str(month)][file]["pdf"]
        except KeyError:
            print("No se encontro el archivo seleccionado")
        if xml is not None and pdf is not None:
            # ask for a path to save
            path = filedialog.askdirectory()
            if path == "":
                return
            settings = json.load(open("files/settings.json", "r"))
            url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
            folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
            download_path_xml, code = download_files_site(
                url_shrpt + folder_rrhh,
                self.data_file_emp["xml"],
                path + "/" + self.selected_file + ".xml",
            )
            download_path_pdf, code = download_files_site(
                url_shrpt + folder_rrhh,
                self.data_file_emp["pdf"],
                path + "/" + self.selected_file + ".pdf",
            )
            if code == 200:
                msg = "Archivos descargados correctamente"
                Messagebox.show_info(title="Info", message=msg)
            else:
                msg = "Error al descargar archivos"
                Messagebox.show_error(title="Error", message=msg)

    def update_months(self, event):
        if event.widget.get() == "No data":
            return
        months = list(self.data_emp_dict[event.widget.get()].keys())
        months = transform_number_month_to_String(months)
        self.entries[2].configure(values=months)

    def update_files(self, event):
        if event.widget.get() == "No data":
            return
        month = event.widget.get()
        month = transform_string_month_to_int([month])[0]
        files = list(self.data_emp_dict[self.entries[1].get()][str(month)].keys())
        self.entries[3].configure(values=files)

    def update_selected_file(self, event):
        if event.widget.get() == "No data":
            return
        self.selected_file = event.widget.get()
        month = self.entries[2].get()
        month = transform_string_month_to_int([month])[0]
        self.data_file_emp = self.data_emp_dict[self.entries[1].get()][str(month)][
            self.selected_file
        ]
        # read xml data
        settings = json.load(open("files/settings.json", "r"))
        url_shrpt = settings["gui"]["RRHH"]["url_shrpt"]
        folder_rrhh = settings["gui"]["RRHH"]["folder_rrhh"]
        download_path_xml, code = download_files_site(
            url_shrpt + folder_rrhh,
            self.data_file_emp["xml"],
            settings["temp_filepath_xml"],
        )
        data_file = get_data_xml_file_nomina(download_path_xml)
        self._svar_txt_date.set(f"Fecha del archivo: {data_file['date']}")
        self._svar_txt_data_pay.set(f"Fecha de pago: {data_file['date_pay']}")
        if "is_send" in self.data_file_emp.keys():
            self._svar_txt_sent.set("Enviado") if self.data_file_emp[
                "is_send"
            ] == 1 else self._svar_txt_sent.set("No Enviado")
        else:
            self._svar_txt_sent.set("No Enviado")

    def update_employees(self):
        flags_daemons = json.load(open(filepath_daemons, "r"))
        if flags_daemons["update_files_nomina"]:
            msg = "Accion no permitida mientras se actualizan los datos."
            Messagebox.show_error(title="Error", message=msg)
            return
        flag, error, result = update_payroll_employees()
        msg = "Se han agregado correctamente:\n"
        counter = 0
        for item in result:
            if item[0]:
                counter += 1
        msg += f"{counter} empleados"
        Messagebox.show_info(title="Empleado Actualizado", message=msg)
        msg = "Los siguientes no se han agregado:\n"
        for item in result:
            if not item[0] and "Duplicate entry" not in str(item[1]):
                msg += f"{item[2]}\n"
        Messagebox.show_error(title="Empleado No Actualizado", message=msg)

    def update_data_table(self):
        flags_daemons = json.load(open(filepath_daemons, "r"))
        if flags_daemons["update_files_nomina"]:
            msg = "Accion no permitida mientras se actualizan los datos."
            Messagebox.show_error(title="Error", message=msg)
            return
        flag, error, result = get_payrolls_with_info(-1)
        data_dic = {
            "payrolls": result,
            "columns_payroll": ["Id", "Nombre", "Apellido", "Datos"],
        }
        self.payrolls_info = data_dic
        self.table_display.destroy()
        self.table_display = self.create_table_display()


class MailCreation(ttk.Toplevel):
    def __init__(self, master=None, email_source=None, emp_destiny_id=None, **kwargs):
        super().__init__(master)
        self.title("Crear Correo")
        self.master = master
        self.email_to_sent = None

        self.columnconfigure((0, 1), weight=1)
        create_label(self, text="Crear Correo", row=0, column=0, font=("Arial", 18))
        create_label(self, text="Destinatarios: ", row=1, column=0)
        self._to = create_entry(self, row=1, column=1)
        if emp_destiny_id is not None:
            flag, error, result = get_emp_mail(emp_destiny_id)
            if flag:
                self._to.insert(0, result[0])
        create_label(self, text="Asunto: ", row=2, column=0)
        self._subject = create_entry(self, row=2, column=1)
        self._subject.insert(0, "RECIBOS NOMINA")
        create_label(self, text="Cuerpo: ", row=3, column=0)
        self._body = ttk.Text(self, height=10, width=50)
        self._body.grid(row=3, column=1, sticky="nsew")
        body_defaul_msg = (
            "Buen día,\n\n"
            "Anexo recibos de nómina correspondientes al mes de JUNIO 2024. Cualquier duda, quedo al pendiente.\n\n"
            "Saludos,\n"
        )
        self._body.insert("1.0", body_defaul_msg)
        create_label(
            self,
            text="Ingrese su correo institucional[@telintec.com.mx]: ",
            row=4,
            column=0,
        )
        self._from = create_entry(self, row=4, column=1)
        if email_source is not None:
            self._from.insert(0, email_source)
        create_button(self, text="Enviar", row=5, column=1, command=self.send_email)

    def send_email(self):
        destinatarios = self._to.get().split(",")
        asunto = self._subject.get()
        cuerpo = self._body.get("1.0", "end-1c")
        _from = self._from.get()
        self.master.create_draft(destinatarios, asunto, cuerpo, _from)
        self.destroy()


class EditPatternsUpdateDataPayroll(ttk.Toplevel):
    def __init__(self, master=None, **kwargs):
        super().__init__(master)
        self.title("Actualizar Datos")
        self.master = master
        self.columnconfigure((0, 1), weight=1)
        create_label(self, text="Actualizar Datos", row=0, column=0, font=("Arial", 18))
        create_label(self, text="Mes: ", row=1, column=0)

        months = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]
        self._patterns_month = create_Combobox(self, values=months, row=1, column=1)
        create_label(self, text="Año: ", row=2, column=0)
        self._patterns_year = create_entry(self, row=2, column=1)
        date_now = datetime.now()
        self._patterns_year.insert(0, str(date_now.year))
        create_label(self, text="Quincena: ", row=3, column=0)
        self._patterns_quincena = create_Combobox(
            self, values=["1Q", "2Q"], row=3, column=1,
        )

        create_button(
            self, text="Actualizar", row=4, column=1, command=self.update_data_action
        )

    def update_data_action(self):
        month = self._patterns_month.get()
        year = self._patterns_year.get()
        quincena = self._patterns_quincena.get()
        patterns = [year, month, quincena]
        self.master.update_data_action(patterns=patterns)
        self.destroy()
