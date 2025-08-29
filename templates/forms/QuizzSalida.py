# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 23/jul./2024  at 5:50 $"

from templates.forms.PDFGenerator import (
    create_datos_personales,
    display_recommendations,
    display_result,
    create_header_telintec,
)
from reportlab.pdfgen import canvas


def QuizzSalidaPDF(
    dict_quizz,
    image_logo=None,
    filepath_out=None,
    name_emp="Ejemplo1",
    job="position 1",
    terminal="terminal",
    date_start="01/01/2021",
    date_end="31/12/2021",
    date_inteview="01/01/2021",
    name_interviewer="Interviewer",
):
    # initializing variables with values
    file_name = "files/quizz_out/sample.pdf" if filepath_out is None else filepath_out
    image_logo = "img/logo_docs.png" if image_logo is None else image_logo
    name_quizz = "Encuesta de Salida"
    # creating a pdf object
    a4_x = 595.27
    a4_y = 841.89
    # create documente
    pdf = canvas.Canvas(file_name, pagesize=(a4_x, a4_y))
    # setting the title of the document
    pdf.setTitle(name_quizz)
    # create header
    create_header_telintec(pdf, image_logo, name_quizz, a4_x, date_inteview)
    # information text
    txt_lines = [
        "Por favor, dedique unos minutos a completar esta encuesta. La información que nos",
        "proporcione será utilizada para entender los motivos de su baja en la empresa.",
        "Sus respuestas serán tratadas de forma CONFIDENCIAL y analizada proactivamente.",
    ]
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(txt_lines):
        pdf.drawString(80, 730 - i * font_size, line)
    # ----------------------question1----------------------
    question = dict_quizz["0"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 680 - i * font_size, line)
    options = dict_quizz["0"]["options"]
    answers = dict_quizz["0"]["answers"] if "answers" in dict_quizz["0"] else [0, 2]
    cols = 3
    for i, option in enumerate(options):
        index_x = i % cols
        index_y = i // cols
        if i in answers:
            pdf.setFillColorRGB(0, 255, 0)
        else:
            pdf.setFillColorRGB(0, 0, 0)
        pdf.drawString(100 + index_x * 140, 640 - index_y * font_size * 1.5, option)
    # ------------------question 2-------------------------
    question = dict_quizz["1"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 555 - i * font_size, line)
    options = dict_quizz["1"]["options"]
    answers = [dict_quizz["1"]["answer"]] if "answer" in dict_quizz["1"] else [2]
    cols = 3
    for i, option in enumerate(options):
        index_x = i % cols
        index_y = i // cols
        if i in answers:
            pdf.setFillColorRGB(0, 255, 0)
        else:
            pdf.setFillColorRGB(0, 0, 0)
        pdf.drawString(100 + index_x * 140, 525 - index_y * font_size * 1.5, option)
    # --------------------question 3-------------------------------
    question = dict_quizz["2"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 490 - i * font_size, line)
    options = dict_quizz["2"]["options"]
    subquestions = dict_quizz["2"]["subquestions"]
    answers = (
        dict_quizz["2"]["answer"]
        if dict_quizz["2"]["answer"] != ""
        else [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0)]
    )
    font_size = 8
    pdf.setFont("Times-Roman", font_size)
    for i, option in enumerate(options):
        option = option.split(" ")
        for j, word in enumerate(option):
            pdf.drawCentredString(250 + i * 70, 450 - j * font_size, word)
    font_size = 11
    pdf.setFont("Times-Roman", font_size)
    for i, subquestion in enumerate(subquestions):
        pdf.drawString(80, 425 - i * font_size * 1.25, subquestion)
    for i in range(len(subquestions)):
        for j in range(len(options)):
            if (i, j) in answers:
                pdf.setFillColorRGB(0, 255, 0)
                pdf.drawString(250 + j * 70, 425 - i * font_size * 1.25, "X")
            else:
                pdf.setFillColorRGB(0, 0, 0)
                pdf.drawString(250 + j * 70, 425 - i * font_size * 1.25, "O")

    # ----------------------question 4-----------------------------------
    question = dict_quizz["3"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 280 - i * font_size, line)
    options = dict_quizz["3"]["options"]
    answers = (
        dict_quizz["3"]["answer"]
        if dict_quizz["3"]["answer"] != ""
        else [(0, 0), (1, 0), (2, 0), (3, 0)]
    )
    subquestions = dict_quizz["3"]["subquestions"]
    font_size = 8
    pdf.setFont("Times-Roman", font_size)
    for i, option in enumerate(options):
        if i == 2:
            option = ["La mitad de", "las veces"]
        else:
            option = option.split(" ")
        for j, word in enumerate(option):
            pdf.drawCentredString(330 + i * 50, 250 - j * font_size, word)
    font_size = 9
    pdf.setFont("Times-Roman", font_size)
    for i, subquestion in enumerate(subquestions):
        subquestion = subquestion.split("\n")
        for j, word in enumerate(subquestion):
            pdf.drawString(40, 225 - i * font_size * 1.35 - j * font_size, word)
    for i in range(len(subquestions)):
        for j in range(len(options)):
            if (i, j) in answers:
                pdf.setFillColorRGB(0, 255, 0)
                pdf.drawString(330 + j * 50, 225 - i * font_size * 1.35, "X")
            else:
                pdf.setFillColorRGB(0, 0, 0)
                pdf.drawString(330 + j * 50, 225 - i * font_size * 1.35, "O")
    # ------------------------question 5------------------------------
    question = dict_quizz["4"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 150 - i * font_size, line)
    options = dict_quizz["4"]["options"]
    answers = (
        dict_quizz["4"]["answer"]
        if dict_quizz["4"]["answer"] != ""
        else [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
    )
    subquestions = dict_quizz["4"]["subquestions"]
    font_size = 8
    pdf.setFont("Times-Roman", font_size)
    for i, option in enumerate(options):
        option = option.split(" ")
        for j, word in enumerate(option):
            pdf.drawCentredString(310 + i * 50, 130 - j * font_size, word)
    font_size = 9
    pdf.setFont("Times-Roman", font_size)
    for i, subquestion in enumerate(subquestions):
        subquestion = subquestion.split("\n")
        for j, word in enumerate(subquestion):
            pdf.drawString(80, 115 - i * font_size * 1.35 - j * font_size, word)
    for i in range(len(subquestions)):
        for j in range(len(options)):
            if (i, j) in answers:
                pdf.setFillColorRGB(0, 255, 0)
                pdf.drawString(310 + j * 50, 115 - i * font_size * 1.35, "X")
            else:
                pdf.setFillColorRGB(0, 0, 0)
                pdf.drawString(310 + j * 50, 115 - i * font_size * 1.35, "O")
    # ----------------------add other page------------------------------------------
    pdf.showPage()
    create_header_telintec(pdf, image_logo, name_quizz, a4_x, date_inteview)
    # ------------------------question 6-------------------
    question = dict_quizz["5"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 730 - i * font_size, line)
    options = dict_quizz["5"]["options"]
    answers = [dict_quizz["5"]["answer"]] if "answer" in dict_quizz["5"] else [2]
    cols = 3
    for i, option in enumerate(options):
        index_x = i % cols
        index_y = i // cols
        if i in answers:
            pdf.setFillColorRGB(0, 255, 0)
        else:
            pdf.setFillColorRGB(0, 0, 0)

        option = (
            option.split("\n")
            if i != 3
            else ["Aprendi en el curso", "de entrenamiento"]
        )

        for j, word in enumerate(option):
            pdf.drawString(
                100 + index_x * 140,
                700 - index_y * font_size * 1.5 - j * font_size,
                word,
            )

    #  ------------------------question 7-------------------
    question = dict_quizz["6"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 645 - i * font_size, line)
    options = dict_quizz["6"]["options"]
    answers = [dict_quizz["6"]["answer"]] if "answer" in dict_quizz["6"] else [2]
    cols = 1
    for i, option in enumerate(options):
        index_x = i % cols
        index_y = i // cols
        if i in answers:
            pdf.setFillColorRGB(0, 255, 0)
        else:
            pdf.setFillColorRGB(0, 0, 0)
        pdf.drawString(120 + index_x * 140, 620 - index_y * font_size * 1.5, option)

    # ------------------------question 8-------------------
    question = dict_quizz["7"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 520 - i * font_size, line)
    options = dict_quizz["7"]["options"]
    answers = [dict_quizz["7"]["answer"]] if "answer" in dict_quizz["7"] else [2]
    cols = 5
    for i, option in enumerate(options):
        index_x = i % cols
        index_y = i // cols
        if i in answers:
            pdf.setFillColorRGB(0, 255, 0)
        else:
            pdf.setFillColorRGB(0, 0, 0)
        pdf.drawString(120 + index_x * 80, 480 - index_y * font_size * 1.5, option)

    # ------------------------question 9-------------------
    question = dict_quizz["8"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 445 - i * font_size, line)
    options = dict_quizz["8"]["options"]
    answers = [dict_quizz["8"]["answer"]] if "answer" in dict_quizz["8"] else [2]
    cols = 5
    for i, option in enumerate(options):
        index_x = i % cols
        index_y = i // cols
        if i in answers:
            pdf.setFillColorRGB(0, 255, 0)
        else:
            pdf.setFillColorRGB(0, 0, 0)
        pdf.drawString(120 + index_x * 80, 400 - index_y * font_size * 1.5, option)

    # ------------------------question 10-------------------
    question = dict_quizz["9"]["question"]
    question = question.split("\n")
    font_size = 12
    pdf.setFont("Times-Roman", font_size)
    for i, line in enumerate(question):
        pdf.drawString(80, 365 - i * font_size, line)
    pdf.line(80, 340, 520, 340)
    pdf.line(80, 340, 80, 200)
    pdf.line(520, 340, 520, 200)
    pdf.line(80, 200, 520, 200)
    answer = dict_quizz["9"]["answer"] if "answer" in dict_quizz["9"] else "No"
    # split every 100 characters
    n_char = 105
    answer = "\n".join([answer[i : i + n_char] for i in range(0, len(answer), n_char)])
    answer = answer.split("\n")
    pdf.setFont("Times-Roman", 10)
    pdf.setFillColorRGB(0, 0, 255)
    for i, line in enumerate(answer):
        pdf.drawString(85, 330 - i * 10, line)
    pdf.setFillColorRGB(0, 0, 0)

    pdf.showPage()
    # ---------------------Resultados-------------------

    display_result(pdf, dict_quizz, 80, 400)

    # ------------------------personal data-------------------
    create_datos_personales(
        pdf,
        name_emp,
        job,
        terminal,
        date_start,
        date_end,
        date_inteview,
        name_interviewer,
        80,
        180,
    )
    display_recommendations(pdf, dict_quizz, 80, 580)
    pdf.save()
    return True
