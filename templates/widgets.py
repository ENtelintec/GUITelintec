import ttkbootstrap as ttk
from ttkbootstrap.constants import *


def create_menu(parent):
    menu = ttk.Frame(parent, border=0)
    ttk.Button(
        menu,
        text="Inicio",
        style="bg.TButton",
        command=lambda: parent.switch_screen(parent._home),
    ).grid(row=0, column=0, sticky="nsew", pady=(16, 0), padx=10)

    ttk.Button(
        menu,
        text="Entradas",
        style="bg.TButton",
        command=lambda: parent.switch_screen(parent._in),
    ).grid(row=1, column=0, sticky="nsew", pady=(16, 0), padx=10)

    ttk.Button(
        menu,
        text="Salidas",
        style="bg.TButton",
        command=lambda: parent.switch_screen(parent._out),
    ).grid(row=2, column=0, sticky="nsew", pady=(16, 0), padx=10)

    ttk.Button(
        menu,
        text="Ordenes",
        style="bg.TButton",
        command=lambda: parent.switch_screen(parent._orders),
    ).grid(row=3, column=0, sticky="nsew", pady=(16, 0), padx=10)

    # ttk.Button(
    #     menu,
    #     text="Devoluciones",
    #     style="bg.TButton",
    #     command=lambda: parent.switch_screen(parent._returns),
    # ).grid(row=4, column=0, sticky="nsew", pady=(16, 0), padx=10)

    ttk.Button(
        menu,
        text="Inventario",
        style="bg.TButton",
        command=lambda: parent.switch_screen(parent._inventory),
    ).grid(row=4, column=0, sticky="nsew", pady=(16, 0), padx=10)

    ttk.Button(
        menu,
        text="Clientes",
        style="bg.TButton",
        command=lambda: parent.switch_screen(parent._clients),
    ).grid(row=5, column=0, sticky="nsew", pady=(16, 0), padx=10)

    ttk.Button(
        menu,
        text="Proveedores",
        style="bg.TButton",
        command=lambda: parent.switch_screen(parent._providers),
    ).grid(row=6, column=0, sticky="nsew", pady=(16, 0), padx=10)

    ttk.Button(
        menu,
        text="Configuracion",
        style="bg.TButton",
        command=lambda: parent.switch_screen(parent._settings),
    ).grid(row=7, column=0, sticky="nsew", pady=(16, 0), padx=10)

    return menu


def create_footer(self):
    footer = ttk.Frame(self, padding=4)
    footer.pack(side="bottom", fill="x")
    ttk.Label(footer, text="Telintec Almacen", style="bg.TLabel").pack(
        side="left", padx=10
    )
    ttk.Label(footer, text="Version 1.0", style="bg.TLabel").pack(side="right", padx=10)
