# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 02/ago./2024  at 0:47 $"

import json
import threading

from static.constants import filepath_daemons
from templates.resources.midleware.Functions_midleware_RRHH import (
    update_data_docs_nomina,
)


class UpdaterSharepointNomina(threading.Thread):
    def __init__(self, patterns):
        super().__init__()
        self.patterns = patterns

    def run(self):
        update_data_docs_nomina(patterns=self.patterns)
        flags_daemons = json.load(open(filepath_daemons, "r"))
        flags_daemons["update_files_nomina"] = False
        json.dump(flags_daemons, open(filepath_daemons, "w"))
