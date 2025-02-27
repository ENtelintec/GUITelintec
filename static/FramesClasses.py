# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/may./2024  at 10:34 $"

from templates.forms.ClimaLaboral import create_quizz_clima_laboral
from templates.forms.Eva360 import create_quizz_eva_360
from templates.forms.QuizzNorm35 import QuizzNor035_v1, QuizzNor035_50Plus
from templates.forms.QuizzSalida import QuizzSalidaPDF
from templates.modules.Administration.DB_Managment import AdminDBFrame
from templates.modules.Administration.SubFrame_ContractCreate import (
    ContractsCreateFrame,
)
from templates.modules.Administration.SubFrame_ContractDocs import ContractsDocsFrame
from templates.modules.Administration.Frame_ControlSaldos import ControlSaldos
from templates.modules.Administration.Frame_Quotations import QuotationsBiddingsFrame
from templates.modules.Administration.Frame_Remisions import RemisionsFrame
from templates.modules.Administration.MainContracts import MainContractFrame
from templates.modules.Administration.PruchaseSales import PurchasesFrame
from templates.modules.Almacen.DashboardStorage import StorageDashboard
from templates.modules.Almacen.Frame_Movements import MovementsFrame
from templates.modules.Bitacora.Frame_Bitacora import BitacoraEditFrame
from templates.modules.Chatbot.Frame_ChatsFrame import ChatFrame
from templates.modules.DB.Frame_DBFrame import DBFrame, EmployeesFrame
from templates.modules.Home.SubFrame_GeneralNoti import NotificationsUser
from templates.modules.Home.SubFrame_NotificationsChatbot import NotificationsChatbot
from templates.modules.Misc.Frame_Tasks import FrameTasks
from templates.modules.RRHH.Frame_EmployeeDetail import EmployeeDetailsScrolled
from templates.modules.RRHH.Frame_Encuestas import EncuestasFrame
from templates.modules.RRHH.Frame_ExamenesMedicos import ExamenesMedicos
from templates.modules.RRHH.Frame_FichajeFilesFrames import FichajesFilesGUI
from templates.modules.Home.Frame_Home import HomeFrame
from templates.modules.Chatbot.Frame_PedidosFrame import PedidosFrame
from templates.modules.RRHH.Frame_Payroll import PayrollFilesGUI
from templates.modules.SM.Frame_SMGeneral import SMFrame
from templates.modules.Misc.Frame_SettingsFrame import SettingsFrameGUI
from templates.modules.RRHH.Frame_Vacations import VacationsFrame
from templates.modules.Assistant.Frame_vAssistantGUI import AssistantGUI
from templates.modules.SM.SubFrame_SMDashboard import SMDashboard
from templates.modules.SM.SubFrame_SMManagement import SMManagement
from templates.modules.Administration.SubFrame_Clients import ClientsScreen
from templates.modules.Almacen.Inventory import InventoryScreen
from templates.modules.Administration.SubFrame_Providers import ProvidersScreen
from templates.modules.Almacen.Supplies import SuppliesScreen
from templates.modules.Sesion.Frame_LoginFrames import LogOptionsFrame

available_frames = {
    "Inicio": HomeFrame,
    "Chats": ChatFrame,
    "Bitacora": BitacoraEditFrame,
    "Vacaciones": VacationsFrame,
    "Encuestas": EncuestasFrame,
    "Exámenes": ExamenesMedicos,
    "Fichajes": FichajesFilesGUI,
    "DB": DBFrame,
    "Empleados": EmployeesFrame,
    "Pedidos": PedidosFrame,
    "Configuración": SettingsFrameGUI,
    "SM": SMFrame,
    "Clientes": ClientsScreen,
    "Proveedores": ProvidersScreen,
    "Inventario": InventoryScreen,
    "Suministros Diarios": SuppliesScreen,
    "Ventana Asistente": AssistantGUI,
    "Examenes": ExamenesMedicos,
    "Emp. Detalles": EmployeeDetailsScrolled,
    "Cuenta": LogOptionsFrame,
    "Procesar SM": SMManagement,
    "Movimientos": MovementsFrame,
    "Settings": SettingsFrameGUI,
    "Tasks": FrameTasks,
    "Pre-Venta": QuotationsBiddingsFrame,
    "Documentos Contrato": ContractsDocsFrame,
    "Control Saldos": ControlSaldos,
    "Remisiones": RemisionsFrame,
    "Nominas": PayrollFilesGUI,
    "Crear Contratos": ContractsCreateFrame,
    "BD Admin": AdminDBFrame,
    "Contratos": MainContractFrame,
    "Compras": PurchasesFrame,
}

frames_notifications_avaliable = {
    "chatbot": NotificationsChatbot,
    "basic": NotificationsUser,
}

avaliable_dashboards = {
    "sm": [SMDashboard],
    "almacen": [StorageDashboard],
    "administracion": [SMDashboard],
}

dict_typer_quizz_generator = {
    0: QuizzSalidaPDF,
    1: QuizzNor035_v1,
    2: QuizzNor035_50Plus,
    3: create_quizz_clima_laboral,
    4: create_quizz_eva_360,
}
