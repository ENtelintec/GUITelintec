# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 23/jul./2024  at 5:53 $'

import textwrap

from reportlab.pdfgen import canvas

from templates.forms.PDFGenerator import create_datos_personales, display_result, display_recommendations, \
    create_header, draw_option


def QuizzNor035_v1(
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
    note_txt = ("*NOTA: Si en esta SECCIÓN  I.- Acontecimiento traumático severo  tu respuesta es NO, "
                "en las siguientes secciones de esta HOJA vas a seleccionar NO a TODAS.")
    file_name = (
        "files/quizz_out/norm035_v1.pdf" if filepath_out is None else filepath_out
    )
    image_logo = "img/logo_docs.png" if image_logo is None else image_logo
    name_quizz = "NORMA 035 V1"
    n_questions = len(dict_quizz)
    interlineado = 0.8
    a4_x = 595.27
    a4_y = 841.89

    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    pdf.setTitle(name_quizz)

    create_header(pdf, image_logo, name_quizz, a4_x, date_interview)

    txt_lines = [
        "CUESTIONARIO PARA IDENTIFICAR A LOS TRABAJADORES QUE FUERON SUJETOS A ",
        "ACONTECIMIENTOS TRAUMÁTICOS SEVEROS",
    ]
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    y_position = 730
    for line in txt_lines:
        pdf.drawString(80, y_position, line)
        y_position -= font_size

    for i in range(n_questions):
        if str(i) not in dict_quizz:
            continue
        if i % 3 == 0 and i != 0:
            pdf.showPage()
            create_header(pdf, image_logo, name_quizz, a4_x, date_interview)
            y_position = 730

        question = textwrap.wrap(dict_quizz[str(i)]["question"], width=121)
        font_size = 10
        pdf.setFont("Times-Roman", font_size)
        y_position -= font_size * interlineado
        for line in question:
            pdf.drawString(40, y_position, line)
            y_position -= font_size * interlineado

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
            pdf.drawString(20, y_position, note_txt)
            pdf.setFillColorRGB(0, 0, 0)
            y_position -= font_size * interlineado

        # pdf.showPage()
        # y_position -= font_size * interlineado

    if i == n_questions - 1:
        # ------------------------personal data-------------------
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


def QuizzNor035_50Plus( 
        dict_quizz, image_logo=None, filepath_out=None, name_emp="Ejemplo1", job="position 1",
        terminal="terminal", date_start="01/01/2021", date_end="31/12/2021", date_interview="01/01/2021", 
        name_interviewer="Interviewer"):
    file_name = (
        "files/quizz_out/norm035_50_plus.pdf"
        if filepath_out is None
        else filepath_out
    )
    image_logo = "img/logo_docs.png" if image_logo is None else image_logo
    name_quizz = "NORMA 035 +50"
    n_questions = len(dict_quizz)
    interlineado = 1
    a4_x = 595.27
    a4_y = 841.89

    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    pdf.setTitle(name_quizz)
    create_header(pdf, image_logo, name_quizz, a4_x, date_interview)

    txt_lines = [
        "CUESTIONARIO PARA IDENTIFICAR A LOS TRABAJADORES QUE FUERON SUJETOS A ",
        "ACONTECIMIENTOS TRAUMÁTICOS SEVEROS",
    ]
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    y_position = 730
    for line in txt_lines:
        pdf.drawString(80, y_position, line)
        y_position -= font_size

    for i in range(n_questions):
        question_data = dict_quizz.get(str(i))
        if question_data:
            # Manejar el control de página cada 3 preguntas basado en el índice 'i'
            if i % 3 == 0 and i != 0:
                pdf.showPage()
                create_header(pdf, image_logo, name_quizz, a4_x, date_interview)
                y_position = 730

            question = textwrap.wrap(question_data["question"], width=121)
            font_size = 11
            pdf.setFont("Times-Roman", font_size)
            y_position -= font_size * interlineado

            for line in question:
                pdf.drawString(40, y_position, line)
                y_position -= font_size

            options = question_data["options"]
            subquestions = question_data["subquestions"]
            answers = (
                question_data["answer"] if question_data["answer"] != "" else [(0, 0)]
            )

            font_size = 8
            pdf.setFont("Times-Roman", font_size)
            y_position -= font_size * interlineado

            # Procesamiento de opciones y subpreguntas aquí
            font_size = 9
            pdf.setFont("Times-Roman", font_size)
            x_subquestion = 20
            x_answers = a4_x / 2 - 10

            for j, option in enumerate(options):
                option_title = f"{option}:"
                pdf.drawCentredString(x_answers + j * 55, y_position, option_title)
            y_position -= font_size * interlineado * 2

            for k, subquestion in enumerate(subquestions):
                lines = textwrap.wrap(subquestion, width=60)
                for m, line in enumerate(lines):
                    pdf.drawString(x_subquestion, y_position, line)
                    if m == 0:
                        draw_option(x_answers, y_position, k, options, answers, pdf)
                    y_position -= font_size * interlineado
                y_position -= font_size * interlineado

            # Asegúrate de añadir otra página si es la última pregunta
        if i == n_questions - 1:
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
        else:
            continue

    pdf.save()
    return True