import threading

# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/may./2024  at 17:04 $"

from datetime import datetime

from templates.controllers.contracts.contracts_controller import get_contract
from templates.controllers.contracts.quotations_controller import get_quotation
from templates.controllers.payroll.payroll_controller import get_payrolls_with_info
from templates.misc.Functions_AuxFiles import (
    get_all_sm_entries,
    get_all_sm_products,
    get_events_op_date,
    get_data_employees,
)
from templates.Functions_AuxPlots import get_data_movements_type, get_data_sm_per_range
from templates.controllers.customer.customers_controller import (
    get_sm_clients,
    get_all_customers_db,
)
from templates.controllers.employees.em_controller import get_all_examenes
from templates.controllers.employees.employees_controller import (
    get_sm_employees,
    get_employees_op_names,
    get_employees,
)
from templates.controllers.employees.vacations_controller import get_vacations_data
from templates.controllers.misc.tasks_controller import get_all_tasks_by_status
from templates.controllers.product.p_and_s_controller import (
    get_all_suppliers,
    get_all_products_db,
    get_ins_db_detail,
    get_outs_db_detail,
    get_all_categories_db,
)
from templates.modules.Home.SubFrame_GeneralNoti import load_notifications
from templates.modules.RRHH.SubFrame_CrearQuiz import get_name_id_employees_list


def load_data(data_dic, is_super=False, emp_id=None, item=None, permissions=None):
    from static.FramesClasses import avaliable_dashboards

    match item:
        case "Inicio":
            # -----------notifications---------------
            data_dic["data_notifications"] = {
                "frame_notifications": load_notifications(emp_id, permissions)
            }
            apps = []
            for value in permissions.values():
                apps.append(value.split(".")[-1].lower())
            data_dic["data_notifications"]["apps"] = apps
            # ------------------dashboards-------------------
            dashboard_key = []
            for permission in permissions.values():
                txt = permission.split(".")
                dashboard_key.append(txt[-1].lower())
            data_dic["data_dashboard"] = {"dashboard_key": dashboard_key}
            created_windows = []
            for dashboard in dashboard_key:
                if dashboard not in avaliable_dashboards.keys():
                    continue
                match dashboard:
                    case "sm":
                        print("sm dashboard data")
                        data_chart = get_data_sm_per_range("year", "normal")
                        data_dic["data_dashboard"][dashboard] = {
                            "data_chart": data_chart
                        }
                    case "almacen":
                        print("almacen dashboard data")
                        data_chart = get_data_movements_type("Entrada", 10)
                        data_dic["data_dashboard"][dashboard] = {
                            "data_chart": data_chart
                        }
                    case "administracion":
                        if "sm" not in data_dic["data_dashboard"].keys():
                            data_chart = get_data_sm_per_range("year", "normal")
                            data_dic["data_dashboard"]["sm"] = {
                                "data_chart": data_chart
                            }
                for window in avaliable_dashboards[dashboard]:
                    if window in created_windows:
                        continue
                    created_windows.append(window)
        case "Bitacora":
            flag, error, emp_data = get_employees_op_names()
            date = datetime.now()
            events, columns = get_events_op_date(date, True)
            data_dic["bitacora"] = {
                "emp_data": emp_data,
                "events": events,
                "columns": columns,
            }
        case "Vacaciones":
            columns = ["emp_id", "name", "l_name", "date_admission", "seniority"]
            flag, error, data = get_vacations_data()
            data_dic["vacaciones"] = {"columns": columns, "data": data}
        case "Encuestas":
            names, emps_metadata = get_name_id_employees_list(1, True)
            data_dic["encuestas"] = {"names": names, "emps_metadata": emps_metadata}
        case "Exámenes":
            columns = [
                "Id_EM",
                "Nombre",
                "Sangre",
                "Estado",
                "Aptitudes",
                "Renovaciones",
                "Apt. Actual",
                "Id_emp",
            ]
            flag, e, out = get_all_examenes()
            data_dic["examenes"] = {"columns": columns, "data": out}
        case "Empleados":
            data = get_employees()
            data_dic["data_emps_gen"] = data
        case "SM":
            data_dic["sm"] = {}
            data_sm, columns_sm = get_all_sm_entries(
                filter_status=False, is_supper=True, emp_id=emp_id
            )
            data_sm_not_supper = []
            if not is_super:
                data_sm_not_supper = [data for data in data_sm if data[7] == emp_id]
            if "data_products_gen" in data_dic:
                columns_products = ("ID", "udm", "Stock", "Nombre")
                products = []
                products_gen = data_dic["data_products_gen"]
                for product in products_gen:
                    products.append((product[0], product[3], product[4], product[2]))
            else:
                products, columns_products = get_all_sm_products()
            if "data_emps_gen" in data_dic:
                employees = []
                for emp_data in data_dic["data_emps_gen"]:
                    if "inactivo" in emp_data[12]:
                        continue
                    employees.append((emp_data[0], emp_data[1], emp_data[2]))
            else:
                flag, error, employees = get_sm_employees()
            flag, error, clients = get_sm_clients()
            data_dic["sm"]["data_sm"] = data_sm
            data_dic["sm"]["columns_sm"] = columns_sm
            data_dic["sm"]["employees"] = employees
            data_dic["sm"]["clients"] = clients
            data_dic["sm"]["columns_products"] = columns_products
            data_dic["sm"]["products"] = products
            data_dic["sm"]["data_sm_not_supper"] = data_sm_not_supper
        case "Clientes":
            flag, error, clients = get_all_customers_db()
            data_dic["data_clients_gen"] = clients
        case "Proveedores":
            flag, error, providers = get_all_suppliers()
            data_dic["data_providers_gen"] = providers
        case "Inventario":
            if "data_products_gen" not in data_dic:
                flag, error, products = get_all_products_db()
                data_dic["data_products_gen"] = products
            if "data_providers_amc" not in data_dic:
                flag, error, providers = get_all_suppliers()
                data_dic["data_providers_gen"] = providers
            if "data_categories_gen":
                flag, error, categories = get_all_categories_db()
                data_dic["data_categories_gen"] = categories
        case "Emp. Detalles":
            data_emp, columns = get_data_employees(status="ACTIVO")
            data_dic["emp_detalles"] = {"data": data_emp, "columns": columns}
        case "Movimientos":
            flag, error, data_movements_in = get_ins_db_detail()
            flag, error, data_movements_out = get_outs_db_detail()
            data_dic["data_movements"] = {
                "data_ins": data_movements_in,
                "data_outs": data_movements_out,
            }
            if "data_products_gen" not in data_dic:
                flag, error, products = get_all_products_db()
                data_dic["data_products_gen"] = products
        case "Tasks":
            flag, error, tasks = get_all_tasks_by_status(status=-1, id_destiny=emp_id)
            data_dic["tasks"] = {"data": tasks}
        case "Cotizaciones":
            if "data_products_gen" not in data_dic:
                flag, error, products = get_all_products_db()
                data_dic["data_products_gen"] = products
            flag, error, data_quotations = get_quotation(None)
            data_dic["quotations"] = data_quotations
        case "Documentos Contrato":
            if "quotations" not in data_dic:
                flag, error, data_quotations = get_quotation(None)
                data_dic["quotations"] = data_quotations
        case "Control Saldos":
            if "contracts" not in data_dic:
                flag, error, contracts = get_contract(None)
                data_dic["contracts"] = contracts
        case "Remisiones":
            data_dic["remisions"] = {}
        case "Nominas":
            flag, error, result = get_payrolls_with_info(-1)
            data_dic["nominas"] = {
                "payrolls": result,
                "columns_payroll": ["Id", "Nombre", "Apellido", "Datos"],
            }
        case "Crear Contratos":
            if "Controlar Saldos" not in data_dic:
                flag, error, contracts = get_contract(None)
                data_dic["contracts"] = contracts
            if "data_clients_gen" not in data_dic:
                flag, error, clients = get_all_customers_db()
                data_dic["data_clients_gen"] = clients
            if "quotations" not in data_dic:
                flag, error, data_quotations = get_quotation(None)
                data_dic["quotations"] = data_quotations
        case _:
            pass
    return data_dic


class DataLoader(threading.Thread):
    def __init__(self, is_super, emp_id, windows, permissions, gui):
        threading.Thread.__init__(self)
        self.is_super = is_super
        self.emp_id = emp_id
        self.windows = windows
        self.permissions = permissions
        self.data_dic = {}
        self._ndata = 0
        self._Ndata = len(self.windows)
        self.gui = gui

    def run(self):
        self.data_dic = self.load_data()

    def get_data(self):
        return self.data_dic

    def load_data(self):
        data_dic = {}
        for item in self.windows:
            data_dic = load_data(
                data_dic, self.is_super, self.emp_id, item, self.permissions
            )
            self._ndata += 1
            self.gui.update_info_loading(self._ndata, self._Ndata)
        self.gui.close_login_frame(data_dic)
        return data_dic

    def get_ndata_loaded(self):
        return self._ndata
