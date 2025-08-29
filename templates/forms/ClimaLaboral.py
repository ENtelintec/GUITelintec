# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/jul./2024  at 5:58 $"

import textwrap

from reportlab.pdfgen import canvas

from templates.forms.PDFGenerator import (
    create_header_telintec,
    create_datos_personales,
    display_result,
    display_recommendations,
    draw_option,
)


def create_quizz_clima_laboral(
    dict_quizz,
    image_logo=None,
    filepath_out=None,
    name_emp="Ejemplo1",
    job="position 1",
    terminal="terminal",
    date_start="01/01/2021",
    date_end="31/12/2021",
    date_interview="01/01/2021",
    name_interviewer="Interviewer",
):
    file_name = (
        "C:/Users/eugen/OneDrive/Escritorio/pdfs/quizz_clima_laboral.pdf"
        if filepath_out is None
        else filepath_out
    )
    image_logo = "img/logo_docs.png" if image_logo is None else image_logo
    name_quizz = "CLIMA LABORAL"
    n_questions = len(dict_quizz)
    interlineado = 1
    a4_x = 595.27
    a4_y = 841.89

    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    pdf.setTitle(name_quizz)

    create_header_telintec(pdf, image_logo, name_quizz, a4_x, date_interview)
    note = "* Indica que la pregunta es obligatoria"
    txt_lines = [
        "OBJETIVO: * ",
        "Conocer la percepción del personal sobre la empresa identificando las áreas ",
        "de oportunidad para poder realizar un plan de acción",
    ]
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    y_position = 730
    for line in txt_lines:
        pdf.drawString(80, y_position, line)
        y_position -= font_size

    for i in range(n_questions):
        question_key = str(i)
        if question_key in dict_quizz:
            question = textwrap.wrap(dict_quizz[question_key]["question"], width=121)
            if i % 3 == 0 and i != 0:
                pdf.showPage()
                create_header_telintec(
                    pdf, image_logo, name_quizz, a4_x, date_interview
                )
                y_position = 730
            question = textwrap.wrap(dict_quizz[str(i)]["question"], width=121)
            font_size = 11
            pdf.setFont("Times-Roman", font_size)
            y_position -= font_size * interlineado

        else:
            continue

        for line in question:
            pdf.drawString(40, y_position, line)
            y_position -= font_size

        options = dict_quizz[str(i)]["options"]
        subquestions = dict_quizz[str(i)]["subquestions"]
        answers = (
            dict_quizz[str(i)]["answer"]
            if dict_quizz[str(i)]["answer"] != ""
            else [(0, 0)]
        )

        font_size = 8
        pdf.setFont("Times-Roman", font_size)
        y_position -= font_size * interlineado
        # Draw subquestions and answers in columns
        x_subquestion = 20
        x_answers = a4_x / 2 - 10

        #  Draw options titles
        for j, option in enumerate(options):
            option_title = f"{option}:"
            pdf.drawCentredString(x_answers + j * 55, y_position, option_title)
        y_position -= font_size * interlineado * 2
        # draw subquestions
        font_size = 9
        pdf.setFont("Times-Roman", font_size)
        for k, subquestion in enumerate(subquestions):
            lines = textwrap.wrap(subquestion, width=60)
            for m, line in enumerate(lines):
                pdf.drawString(x_subquestion, y_position, line)
                if m == 0:
                    draw_option(x_answers, y_position, k, options, answers, pdf)
                y_position -= font_size * interlineado
            y_position -= font_size * interlineado

        if i == 0:
            font_size = 8
            pdf.setFillColorRGB(255, 0, 0)
            pdf.setFont("Times-Roman", font_size)
            pdf.drawString(20, y_position, note)
            pdf.setFillColorRGB(0, 0, 0)
            y_position -= font_size * interlineado

    if i == n_questions - 1:
        # ------------------------personal data-------------------
        pdf.showPage()
        create_datos_personales(
            pdf,
            name_emp,
            job,
            terminal,
            date_start,
            date_end,
            date_interview,
            name_interviewer,
            80,
            180,
        )
        display_result(pdf, dict_quizz, 80, 400)
        display_recommendations(pdf, dict_quizz, 80, 580)

    pdf.save()
    return True
