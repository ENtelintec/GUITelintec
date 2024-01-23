from templates.widgets import *


class ReturnsScreen(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, style="bg.TFrame")
        self.master = master
        self.grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.create_content(self)

    def create_content(self, parent):
        """Creates the content of the Returns screen, includes the table of returns and the inputs to modify a return"""

        content = ttk.Frame(parent, style="bg.TFrame")
        content.pack(side="left", fill="both", expand=True)
        ttk.Label(content, text="Devoluciones", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        # Table
        table = ttk.Frame(content, style="bg.TFrame")
        table.pack(side="top", fill="both", expand=True)
        ttk.Label(table, text="Tabla de devoluciones", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        # Inputs
        inputs = ttk.Frame(content, style="bg.TFrame")
        inputs.pack(side="top", fill="both", expand=True)
        ttk.Label(inputs, text="Modificar devolucion", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs, text="Producto", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Combobox(inputs, values=["Producto 1", "Producto 2"]).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs, text="Cantidad", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Entry(inputs).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Label(inputs, text="Fecha de devolucion", style="bg.TLabel").pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        ttk.Entry(inputs).pack(
            side="top", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )

        # Buttons
        buttons = ttk.Frame(content, style="bg.TFrame")
        buttons.pack(side="top", fill="y", expand=True)
        ttk.Button(buttons, text="Agregar", style="bg.TButton", width=25).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        ttk.Button(buttons, text="Editar", style="bg.TButton", width=25).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        ttk.Button(buttons, text="Eliminar", style="bg.TButton", width=25).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
        ttk.Button(buttons, text="Limpiar", style="bg.TButton", width=25).pack(
            side="left", fill="x", anchor="center", ipady=5, pady=(16, 0), padx=10
        )
