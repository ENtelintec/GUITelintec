# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 22/ene./2024  at 16:09 $'

import os
from PIL import Image
from customtkinter import CTkImage

carpeta_principal = "./img"


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
        "Tickets": "ticket_light.png",
        "Fichajes": "fichaje.png",
        "Cuenta": "user_robot.png",
        "Examenes": "exam_medical.png",
        "Emp. Detalles": "emp_details_dark.png",
        "Home": "warehouse_white.png",
        "Clients (A)": "warehouse_white.png",
        "Inventario": "warehouse_white.png",
        "Entradas": "warehouse_white.png",
        "Salidas": "warehouse_white.png",
        "Devoluciones": "warehouse_white.png",
        "Ordenes (A)": "warehouse_white.png",
        "Proveedores (A)": "warehouse_white.png",
        "Configuraciones (A)": "warehouse_white.png",
        "messenger": "messenger.png",
        "whasapp":  "whasapp.png",
        "telegram": "telegram.png",
        "webchat": "webchat.png",
        "logo":  "telintec-500.png"
    }
    if wname in images.keys():
        return CTkImage(light_image=Image.open(os.path.join(image_path, images[wname])),
                        size=(30, 30))
    else:
        return CTkImage(light_image=Image.open(os.path.join(image_path, images["DB"])),
                        size=(30, 30))


def load_default_images():
    """
    Load the default images for the buttons.
    :return: A list of images.
    :rtype: List of images.
    """
    image_path = carpeta_principal
    return (CTkImage(Image.open(os.path.join(image_path, "telintec-500.png")), size=(90, 90)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "bd_img_col_!.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "not_img_col_re.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "chat_light.png")),
                     dark_image=Image.open(os.path.join(image_path, "chat_light.png")),
                     size=(20, 20)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "settings.png")),
                     size=(40, 40)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "fichaje.png")),
                     dark_image=Image.open(os.path.join(image_path, "fichaje.png")),
                     size=(40, 40)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "user_robot.png")),
                     dark_image=Image.open(os.path.join(image_path, "user_robot.png")),
                     size=(40, 40)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "messenger.png")),
                     dark_image=Image.open(os.path.join(image_path, "messenger.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "whatsapp.png")),
                     dark_image=Image.open(os.path.join(image_path, "whatsapp.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "telegram.png")),
                     dark_image=Image.open(os.path.join(image_path, "telegram.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "webchat.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "pedido_img.png")),
                     dark_image=Image.open(os.path.join(image_path, "pedido_img.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "iso_claro.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "exam_medical.png")),
                     size=(40, 40)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "warehouse_black.png")),
                     dark_image=Image.open(os.path.join(image_path, "warehouse_white.png")),
                     size=(30, 30)),
            CTkImage(light_image=Image.open(os.path.join(image_path, "emp_details_dark.png")),
                     size=(30, 30))
            )
