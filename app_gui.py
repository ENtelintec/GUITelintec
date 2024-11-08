# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 06/feb./2024  at 9:14 $"

import faulthandler

from templates import GUIGeneral
from wtforms_json import init as init_wtforms_json

init_wtforms_json()

if __name__ == "__main__":
    faulthandler.enable()
    main = GUIGeneral.GUIAsistente()
    main.state("zoomed")
    main.mainloop()
