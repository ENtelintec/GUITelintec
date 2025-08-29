# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/feb./2024  at 15:54 $"

import json
import textwrap

from reportlab.pdfgen import canvas

from static.constants import filepath_settings

a4_x = 595.27
a4_y = 841.89
image_logo = "img/logo_docs.png"


def create_datos_personales(
    master: canvas.Canvas,
    emp,
    puesto,
    term,
    start,
    end,
    interview,
    interviewer,
    dim_x,
    dim_y,
):
    pady = 0
    master.setFont("Courier-Bold", 10)
    master.drawString(dim_x + 10, dim_y - 25 - pady, "Nombre y firma del empleado:")
    master.drawString(dim_x + 10, dim_y - 40 - pady, "Puesto:")
    master.drawString(dim_x + 10, dim_y - 55 - pady, "Terminal:")
    master.drawString(dim_x + 10, dim_y - 70 - pady, "Fecha de inicio:")
    master.drawString(dim_x + 10, dim_y - 85 - pady, "Fecha de fin:")
    master.drawString(dim_x + 10, dim_y - 100 - pady, "De entrevista:")
    master.drawString(
        dim_x + 10, dim_y - 115 - pady, "Nombre y firma del entrevistador:"
    )
    master.setFont("Courier", 10)
    master.drawString(dim_x + 180, dim_y - 25 - pady, emp)
    master.drawString(dim_x + 60, dim_y - 40 - pady, puesto)
    master.drawString(dim_x + 70, dim_y - 55 - pady, term)
    master.drawString(dim_x + 110, dim_y - 70 - pady, start)
    master.drawString(dim_x + 95, dim_y - 85 - pady, end)
    master.drawString(dim_x + 105, dim_y - 100 - pady, f"{interview}")
    master.drawString(dim_x + 215, dim_y - 115 - pady, f"{interview}")


def print_footer_page_count(pdf, page, font_size=6, right_text="", x_max=a4_x):
    """
    :param x_max:
    :param right_text:
    :param pdf:
    :param page:
    :param font_size:
    :return:
    """
    pdf.setFont("Courier", font_size)
    pdf.drawString(5, 5, f"Página {page}")
    if right_text != "":
        pdf.drawString(x_max - len(right_text) * font_size * 0.7, 5, right_text)


def display_result(master: canvas.Canvas, dict_quizz, dim_x, dim_y):
    dict_results = dict_quizz["results"]
    # Posición inicial de la primera línea
    pady = 0
    master.setFont("Helvetica", 10)
    master.drawString(dim_x + 10, dim_y - 140 - pady, "Your final result is:")
    master.drawString(
        dim_x + 10,
        dim_y - 155 - pady,
        f"Calificación final: {wrap_text(str(dict_results['c_final']))}",
    )
    master.drawString(
        dim_x + 10,
        dim_y - 170 - pady,
        f"Calificación de dominio:{wrap_text(str(dict_results['c_dom']))}",
    )
    master.drawString(
        dim_x + 10,
        dim_y - 185 - pady,
        f"Calificacion de categoria: {wrap_text(str(dict_results['c_cat']))}",
    )


def wrap_text(text, width=30):
    return "\n".join(textwrap.wrap(text, width=width))


def display_recommendations(master: canvas.Canvas, dict_quizz, dim_x, dim_y):
    dict_recommendations = dict_quizz["recommendations"]
    pady = 0
    master.setFont("Helvetica", 10)
    master.drawString(dim_x + 10, dim_y - 200 - pady, "Recomendaciones:")
    master.drawString(
        dim_x + 10,
        dim_y - 215 - pady,
        f"Recomendacion para calificación final:{dict_recommendations['c_final_r']}",
    )
    master.drawString(
        dim_x + 10,
        dim_y - 230 - pady,
        f"Recomendacion para calificación de dominio:{dict_recommendations['c_dom_r']}",
    )
    master.drawString(
        dim_x + 10,
        dim_y - 245 - pady,
        f"Recomendacion para calificación de categoria:{dict_recommendations['c_cat_r']}",
    )


def create_header_telintec(
    master: canvas.Canvas,
    img=None,
    title=None,
    page_x=None,
    date_int=None,
    iso_form=1,
    orientation="vertical",
    title_font=None,
    offset_title=(0, 0),
):
    position_header_y = 770 if orientation == "vertical" else 535
    position_header_x = 25 if orientation == "vertical" else 25
    height_logo = 30
    title_height = 16 if title_font is None else title_font
    codes_h_height = 10
    codes_width = 150  # right codes and emision width
    start_box_x = 10 if orientation == "vertical" else 10
    height_box = 50
    pady = 10
    padx = 15
    width_logo = 106.6
    img = img if img is not None else image_logo
    # header
    # bottom line
    master.line(
        start_box_x,
        position_header_y + height_box - pady,
        page_x - start_box_x,
        position_header_y + height_box - pady,
    )
    # first vertical line
    master.line(
        start_box_x,
        position_header_y + height_box - pady,
        start_box_x,
        position_header_y - pady,
    )
    # last vertical line
    master.line(
        page_x - start_box_x,
        position_header_y + height_box - pady,
        page_x - start_box_x,
        position_header_y - pady,
    )
    # top line
    master.line(
        start_box_x,
        position_header_y - pady,
        page_x - start_box_x,
        position_header_y - pady,
    )
    # first separator
    master.line(
        start_box_x + (position_header_x - start_box_x) + width_logo + padx,
        position_header_y + height_box - pady,
        start_box_x + (position_header_x - start_box_x) + width_logo + padx,
        position_header_y - pady,
    )
    # second separator
    master.line(
        page_x - start_box_x - codes_width - padx,
        position_header_y + height_box - pady,
        page_x - start_box_x - codes_width - padx,
        position_header_y - pady,
    )
    # logo
    master.drawInlineImage(
        img,
        position_header_x,
        position_header_y,
        height=30,
        width=106.6,
        preserveAspectRatio=False,
        showBoundary=False,
    )
    if isinstance(title, str):
        title = title.upper()
        master.setFont("Courier-Bold", title_height)
        master.drawCentredString(
            page_x / 2 + offset_title[0],
            position_header_y + height_logo / 2 - title_height / 2 + offset_title[1],
            title.upper(),
        )
    else:
        nlines = len(title)
        x_title = page_x / 2 + offset_title[0]
        y_title = (
            position_header_y + height_logo / 2 + ((nlines - 1) * title_height) / 2
        ) + offset_title[1]
        for index, line in enumerate(title):
            master.setFont("Courier-Bold", title_height - 2 * index)
            master.drawCentredString(x_title, y_title, line)
            y_title -= title_height
    master.setFont("Courier", codes_h_height)
    settings = json.load(open(filepath_settings, "r"))
    dict_codes_forms = settings["formats"]["dict_codes_forms"]
    master.drawString(
        page_x - codes_width - padx,
        position_header_y + height_logo - codes_h_height,
        f"Codigo: {dict_codes_forms[str(iso_form)]}",
    )
    dict_dates = settings["formats"]["dates_emision"]
    master.drawString(
        page_x - codes_width - padx,
        position_header_y,
        f"I. Vigencia: {dict_dates[str(iso_form)]}",
    )


def create_header_materials(
    master: canvas.Canvas,
    img=None,
    title=None,
    page_x=None,
    date_int=None,
    type_form=1,
    orientation="vertical",
    title_font=None,
    info_dict=None,
):
    position_header_y = 770 if orientation == "vertical" else 535
    position_header_x = 25 if orientation == "vertical" else 25
    height_logo = 30
    title_height = 16 if title_font is None else title_font
    codes_h_height = 10
    codes_width = 140
    start_box_x = 10 if orientation == "vertical" else 10
    height_box = 50
    pady = 10
    padx = 15
    width_logo = 106.6
    img = img if img is not None else image_logo
    # header
    # bottom line
    master.line(
        start_box_x,
        position_header_y + height_box - pady,
        page_x - start_box_x,
        position_header_y + height_box - pady,
    )
    # first vertical line
    master.line(
        start_box_x,
        position_header_y + height_box - pady,
        start_box_x,
        position_header_y - pady,
    )
    # last vertical line
    master.line(
        page_x - start_box_x,
        position_header_y + height_box - pady,
        page_x - start_box_x,
        position_header_y - pady,
    )
    # top line
    master.line(
        start_box_x,
        position_header_y - pady,
        page_x - start_box_x,
        position_header_y - pady,
    )
    # first separator
    master.line(
        start_box_x + (position_header_x - start_box_x) + width_logo + padx,
        position_header_y + height_box - pady,
        start_box_x + (position_header_x - start_box_x) + width_logo + padx,
        position_header_y - pady,
    )
    # second separator
    master.line(
        page_x - start_box_x - codes_width - padx,
        position_header_y + height_box - pady,
        page_x - start_box_x - codes_width - padx,
        position_header_y - pady,
    )
    # logo
    master.drawInlineImage(
        img,
        position_header_x,
        position_header_y,
        height=30,
        width=106.6,
        preserveAspectRatio=False,
        showBoundary=False,
    )
    if isinstance(title, str):
        title = title.upper()
        master.setFont("Courier-Bold", title_height)
        master.drawCentredString(
            page_x / 2,
            position_header_y + height_logo / 2 - title_height / 2,
            title.upper(),
        )
    else:
        nlines = len(title)
        x_title = page_x / 2
        y_title = (
            position_header_y + height_logo / 2 + ((nlines - 1) * title_height) / 2
        )
        for index, line in enumerate(title):
            master.setFont("Courier-Bold", title_height - 2 * index)
            master.drawCentredString(x_title, y_title, line)
            y_title -= title_height
    master.setFont("Courier", codes_h_height)
    settings = json.load(open(filepath_settings, "r"))
    dict_codes_forms = settings["formats"]["dict_codes_forms"]
    master.drawString(
        page_x - codes_width - padx,
        position_header_y + height_logo - codes_h_height,
        f"Codigo: {dict_codes_forms[str(type_form)]}",
    )
    dict_dates = settings["formats"]["dates_emision"]
    master.setFont("Courier", 8)
    master.drawString(
        page_x - codes_width - padx * 1.2,
        position_header_y,
        f"Inicio de Vigencia: {dict_dates[str(type_form)]}",
    )
    # --------------------------------datos quien devuelve------------------------------------
    font_size = 10
    position_header_y -= font_size * 1.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(
        position_header_x,
        position_header_y - 10,
        "Datos del empleado que realiza la devolución",
    )
    position_header_y -= font_size * 2.5
    master.setFont("Courier", font_size)
    master.drawString(
        position_header_x, position_header_y, f"Nombre:  {info_dict['emp_name']}"
    )
    master.drawString(
        position_header_x,
        position_header_y - font_size * 1.5,
        f"Contrato:  {info_dict['contrato']}",
    )
    master.drawString(
        page_x - codes_width - padx, position_header_y, f"Fecha:  {info_dict['date']}"
    )
    master.drawString(
        page_x - codes_width - padx,
        position_header_y - font_size * 1.5,
        f"Lugar:  {info_dict['lugar']}",
    )
    position_header_y -= font_size * 3.5
    master.setFont("Courier-Bold", font_size)
    master.drawString(
        position_header_x, position_header_y, "Datos del quien recibe la devolucion"
    )
    position_header_y -= font_size * 2.5
    master.setFont("Courier", font_size)
    master.drawString(
        position_header_x,
        position_header_y,
        f"Nombre:  {info_dict['emp_storage_name']}",
    )
    master.drawString(
        position_header_x,
        position_header_y - font_size * 1.5,
        f"Puesto:  {info_dict['puesto']}",
    )
    master.drawString(
        page_x - codes_width - padx, position_header_y, "Tipo de devolición:"
    )
    master.drawString(
        page_x - codes_width - padx,
        position_header_y - font_size * 1.5,
        f"{info_dict['type_return']}",
    )


def create_info_materials_request(
    master: canvas.Canvas,
    info_dict,
    position_header_x,
    position_header_y,
    orientation="vertical",
    font_size=10,
    keys_inf=None,
):
    page_x = a4_x if orientation == "vertical" else a4_y
    keys_info = keys_inf if keys_inf is not None else list(info_dict.keys())
    columns = 2
    nrows = len(keys_info) // columns + (len(keys_info) % columns > 0)
    y_init = position_header_y
    for index, key in enumerate(keys_info):
        column = 0 if index < nrows else 1
        position_header_y = y_init if index % nrows == 0 else position_header_y
        index_y = index % nrows
        master.setFont("Courier-Bold", font_size)
        master.drawString(
            position_header_x + (page_x / 2 - 20) * column,
            position_header_y,
            f"{key.upper()}:",
        )

        master.setFont("Courier", font_size)
        master.drawString(
            position_header_x + len(key) * font_size * 0.7 + (page_x / 2 - 20) * column,
            position_header_y,
            f"{info_dict[key]}",
        )
        position_header_y -= font_size * 1.5


def draw_option(x, y, k, options, answers, pdf):
    if not isinstance(answers, (list, set)):
        answers = [answers]  # Convertir a lista si es un entero

    for j, option in enumerate(options):
        if (k, j) in answers:
            pdf.setFillColorRGB(0, 255, 0)
            pdf.drawCentredString(x + j * 55, y, "X")
        else:
            pdf.setFillColorRGB(0, 0, 0)
            pdf.drawCentredString(x + j * 55, y, "O")


def create_footer_sign(pdf, position_x, position_y, text="Firma"):
    pdf.setFont("Courier", 10)
    pdf.drawString(position_x, position_y, text)
    pdf.line(
        position_x - 20,
        position_y + 15,
        position_x + len(text) * 10 * 0.65 + 20,
        position_y + 15,
    )
