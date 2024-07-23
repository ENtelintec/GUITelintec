# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/feb./2024  at 15:54 $"

import textwrap

from reportlab.pdfgen import canvas


a4_x = 595.27
a4_y = 841.89
image_logo = "img/logo_docs.png" 
dict_codes_forms = {
    1: "FO-GRH-08 R0",
    2: "FO-ALM-03 R0",
    3: "FO-GRH-08 R0",
}


def create_datos_personales(
        master: canvas.Canvas, emp, puesto, term, start, end, interview, interviewer, dim_x, dim_y):
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


def create_header(master: canvas.Canvas, img=None, title=None, page_x=None, date_int=None, 
                  type_form=1, orientation="vertical", title_font=None):
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
        y_title = position_header_y + height_logo / 2 + ((nlines-1) * title_height) / 2
        for index, line in enumerate(title):
            master.setFont("Courier-Bold", title_height-2*index)
            master.drawCentredString(x_title, y_title, line)
            y_title -= title_height
    master.setFont("Courier", codes_h_height)
    master.drawString(
        page_x - codes_width - padx,
        position_header_y + height_logo - codes_h_height,
        f"Codigo: {dict_codes_forms[type_form]}",
    )
    master.drawString(
        page_x - codes_width - padx, position_header_y, f"Emisión: {date_int}"
    )


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


