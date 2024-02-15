# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 22/ene./2024  at 16:09 $'

from PIL import Image, ImageTk

from templates.Functions_Files import get_fichajes_resume_cache

carpeta_principal = "img"


def get_image_side_menu(wname, image_path=carpeta_principal):
    """
    Get the image for the side menu.
    :param wname: The name of the window.
    :type wname: String.
    :param image_path: The path of the image.
    :type image_path: String.
    :return: The image.
    :rtype: CTkImage.
    """
    images = {
        "DB": "bd_img_col_!.png",
        "Notificaciones": "not_img_col_re.png",
        "Chats": "chat_light.png",
        "Settings": "settings_light.png",
        "Fichajes": "fichaje.png",
        "Cuenta": "user_robot.png",
        "Examenes": "exam_medical.png",
        "Emp. Detalles": "emp_details_dark.png",
        "Home": "warehouse_white.png",
        "Clients (A)": "employees_ligth.png",
        "Inventario": "products_ligth.png",
        "Entradas": "incoming.png",
        "Salidas": "out_p.png",
        "Devoluciones": "return_p.png",
        "Ordenes (A)": "order_p.png",
        "Proveedores (A)": "providers_p.png",
        "Configuraciones (A)": "settings.png",
        "messenger": "messenger.png",
        "whasapp":  "whasapp.png",
        "telegram": "telegram.png",
        "webchat": "webchat.png",
        "logo":  "telintec-500.png",
        "Empleados":  "customers_ligth.png",
        "Clientes":  "employees_ligth.png",
        "Departamentos": "departments_ligth.png",
        "Encargados": "heads_ligth.png",
        "Proveedores": "suppliers_ligth.png",
        "Productos": "products_ligth.png",
        "Ordenes": "orders_img.png",
        "Compras": "purchases_img.png",
        "Tickets": "ticket_img.png",
        "Chat": "chats_img.png",
        "O. Virtuales": "v_orders_img.png",
        "Usuarios": "add_user_light.png"
    }
    if wname in images.keys():
        if wname == "logo":
            image = Image.open(image_path + "/" + images[wname])
            resize_img = image.resize((100, 80))
            out_img = ImageTk.PhotoImage(resize_img)
            return out_img
            # return CTkImage(light_image=Image.open(os.path.join(image_path, images[wname])),
            #                 size=(80, 60))
        image = Image.open(image_path + "/" + images[wname])
        resize_img = image.resize((30, 30))
        out_img = ImageTk.PhotoImage(resize_img)
        return out_img
        # return CTkImage(light_image=Image.open(os.path.join(image_path, images[wname])),
        #                 size=(30, 30))
    else:
        image = Image.open(image_path + "/" + images["DB"])
        resize_img = image.resize((30, 30))
        out_img = ImageTk.PhotoImage(resize_img)
        return out_img
        # return CTkImage(light_image=Image.open(os.path.join(image_path, images["DB"])),
        #                 size=(30, 30))


def get_data_employees(status="ACTIVO"):
    columns = ("ID", "Nombre", "Contrato", "Faltas", "Tardanzas", "Dias Extra", "Total", "Primas",
               "Detalles Faltas", "Detalles Tardanzas", "Detalles Extras", "Detalles Primas")
    fichajes_resume, flag = get_fichajes_resume_cache("files/fichajes_resume_cache.pkl")
    if flag:
        return fichajes_resume, columns
    else:
        print("error at getting data resume")
        return None, None
