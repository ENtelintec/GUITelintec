import ttkbootstrap as ttk
from PIL import Image

from templates.Functions_AuxPlots import get_data_movements_type
from templates.Funtions_Utils import create_label, create_Combobox
from templates.modules.Misc.SubFrame_Plots import FramePlot

Image.CUBIC = Image.BICUBIC


class StorageDashboard(ttk.Frame):
    def __init__(self, master, setting: dict = None, *args, **kwargs):
        super().__init__(master)
        self.master = master
        self.plots = []
        self._svar_selector = ttk.StringVar(value="Entrada")
        self.columnconfigure((0, 1), weight=1)
        create_label(self, 0, 0, text="Almacen dashboard", font=("Helvetica", 18, "bold"))
        frame_selector = ttk.Frame(self)
        frame_selector.grid(row=0, column=0, sticky="nswe")
        frame_selector.columnconfigure(0, weight=1)
        selector_type = create_Combobox(frame_selector, ["Entrada", "Salida"], textvariable=self._svar_selector,
                                        row=0, column=0, sticky="n")
        selector_type.bind("<<ComboboxSelected>>", self.re_plot)
        self.frame_plots = ttk.Frame(self)
        self.frame_plots.grid(row=1, column=0, sticky="nswe")
        self.frame_plots.columnconfigure(0, weight=1)
        self.create_plots(self.frame_plots, self._svar_selector.get(), 10, kwargs["data"]["data_dashboard"]["almacen"]["data_chart"])

    def create_plots(self, master, type_m, n_val, data_chart=None):
        if len(self.plots) > 0:
            for plot in self.plots:
                plot.destroy()
        self.plots = []
        data_chart = get_data_movements_type(type_m, n_val) if data_chart is None else data_chart
        plot1_1 = FramePlot(master, data_chart, "bar")
        plot1_1.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
        self.plots.append(plot1_1)

    def re_plot(self, event):
        value = event.widget.get()
        self.create_plots(self.frame_plots, value, 10)
