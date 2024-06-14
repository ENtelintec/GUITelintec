# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 14/jun./2024  at 11:16 $'

from PIL import Image, ImageTk
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
        "DB": "DB.png",
        "Notificaciones": "Notificacion.png",
        "Settings": "Settings.png",
        "Fichajes": "RH/Fichajes.png",
        "Cuenta": "Cuenta.png",
        "Examenes": "RH/Examenes.png",
        "Emp. Detalles": "RH/DetallesEmpleados.png",
        "Home": "Inicio.png",
        "Clientes": "Almacenes/Clientes.png",
        "Inventario": "Almacenes/Inventario.png",
        "Entradas": "Almacenes/Entradas.png",
        "Salidas": "Almacenes/Salidas.png",
        "Proveedores": "Almacenes/proveedores.png",
        "messenger": "messenger.png",
        "whatsapp": "whasapp.png",
        "telegram": "telegram.png",
        "facebook":  "messenger.png",
        "webchat": "webchat.png",
        "logo": "LogoTelintec.png",
        "Empleados": "RH/Empleados.png",
        "Inicio": "Inicio.png",
        "Encuestas": "RH/Encuestas.png",
        "Exámenes": "RH/Examenes.png",
        "Vacaciones": "RH/Vacaciones.png",
        "Procesar SM": "Almacenes/ProcesamientoSM.png",
        "Movimientos": "Almacenes/Movimientos.png",
        "SM": "Almacenes/SM.png",
        "Departamentos": "DB/Departamentos.png",
        "Encargados": "DB/Encargados.png",
        "Productos": "DB/Productos.png",
        "Ordenes": "DB/Ordenes.png",
        "Tickets": "DB/tickets.png",
        "O. Virtuales": "DB/Ordenes.png"
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
        print(f"image for icon not found: {wname}")
        image = Image.open(image_path + "/" + images["DB"])
        resize_img = image.resize((30, 30))
        out_img = ImageTk.PhotoImage(resize_img)
        return out_img
        # return CTkImage(light_image=Image.open(os.path.join(image_path, images["DB"])),
        #                 size=(30, 30))
