# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/may./2024  at 10:34 $"

from templates.forms.ClimaLaboral import create_quizz_clima_laboral
from templates.forms.Eva360 import create_quizz_eva_360
from templates.forms.QuizzNorm35 import QuizzNor035_v1, QuizzNor035_50Plus
from templates.forms.QuizzSalida import QuizzSalidaPDF

dict_typer_quizz_generator = {
    0: QuizzSalidaPDF,
    1: QuizzNor035_v1,
    2: QuizzNor035_50Plus,
    3: create_quizz_clima_laboral,
    4: create_quizz_eva_360,
}
