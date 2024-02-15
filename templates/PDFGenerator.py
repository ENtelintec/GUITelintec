# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 14/feb./2024  at 15:54 $'

import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.pdfgen import canvas


def create_header(master, img, title, page_x):
    position_header_y = 790
    position_header_x = 25
    height_logo = 30
    title_height = 16
    codes_h_height = 10
    codes_width = 140
    start_box_x = 10
    height_box = 50
    pady = 10
    padx = 15
    width_logo = 106.6
    # header
    master.line(start_box_x, position_header_y + height_box - pady,
                page_x - start_box_x, position_header_y + height_box - pady)
    master.line(start_box_x, position_header_y + height_box - pady,
                start_box_x, position_header_y - pady)
    master.line(page_x - start_box_x, position_header_y + height_box - pady,
                page_x - start_box_x, position_header_y - pady)
    master.line(start_box_x, position_header_y - pady,
                page_x - start_box_x, position_header_y - pady)
    master.line(start_box_x + (position_header_x - start_box_x) + width_logo + padx,
                position_header_y + height_box - pady,
                start_box_x + (position_header_x - start_box_x) + width_logo + padx, position_header_y - pady)
    master.line(page_x - start_box_x - codes_width - padx, position_header_y + height_box - pady,
                page_x - start_box_x - codes_width - padx, position_header_y - pady)
    master.drawInlineImage(img, position_header_x, position_header_y,
                           height=30, width=106.6,
                           preserveAspectRatio=False, showBoundary=False)
    master.setFont("Courier-Bold", title_height)
    master.drawCentredString(
        page_x / 2, position_header_y + height_logo / 2 - title_height / 2, title.upper())
    master.setFont("Courier", codes_h_height)
    master.drawString(page_x - codes_width - padx, position_header_y + height_logo - codes_h_height,
                      'Codigo: FO-GRH-08 R0')
    master.drawString(page_x - codes_width - padx, position_header_y, f'Emisión: {datetime.now().strftime("%d/%m/%Y")}')


def create_question(master, question, options, correct, index, type_q):
    master.setFont("Courier", 14)
    master.drawAlignedString(30, 700 - (index * 30), question, 'Q.' + str(index + 1))
    master.setFont("Courier", 12)
    for i, option in enumerate(options):
        master.drawCentredString(290, 720 - (index * 30) - (i * 30), option)
    master.setFont("Courier", 14)
    master.drawCentredString(290, 720 - (index * 30) - (len(options) * 30), f'Correcta: {correct}')


# initializing variables with values
fileName = 'C:/Users/Edisson/Documents/sample.pdf'
documentTitle = 'sample'
subTitle = 'The largest thing now!!'
textLines = [
    'Technology makes us aware of',
    'the world around us.',
]
image_logo = '../img/logo_docs.png'
name_quizz = 'Encuesta de Salida'
dict_quizz = json.load(open('../files/quizz_salida.json', encoding="utf-8"))
n_questions = len(dict_quizz)

# creating a pdf object
A4_x = 595.27
A4_y = 841.89

# create documente
pdf = canvas.Canvas(fileName, pagesize=(A4_x, A4_y))
create_header(pdf, image_logo, name_quizz, A4_x)
# setting the title of the document
pdf.setTitle(name_quizz)
# questions
for i, item in enumerate(dict_quizz.values()):
    create_question(pdf, item['question'], item['options'], item['answer'], i, item['type'])
# creating the subtitle by setting it's font,
# colour and putting it on the canvas
pdf.showPage()
pdf.setFillColorRGB(0, 0, 255)
pdf.setFont("Courier-Bold", 24)
pdf.drawCentredString(290, 720, subTitle)
# drawing a line
pdf.line(30, 710, 550, 710)

# creating a multiline text using
# textline and for loop
text = pdf.beginText(40, 680)
text.setFont("Courier", 18)
text.setFillColor(colors.red)

for line in textLines:
    text.textLine(line)

pdf.drawText(text)

# saving the pdf
pdf.showPage()
# add other page
pdf.setTitle("other title")
pdf.setFont("Courier-Bold", 24)
pdf.drawCentredString(300, 794, name_quizz)
pdf.showPage()
pdf.showPage()
pdf.save()
