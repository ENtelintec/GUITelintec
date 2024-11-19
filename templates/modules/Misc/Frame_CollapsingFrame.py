# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 15/nov./2023  at 13:03 $"

import ttkbootstrap as ttk
from ttkbootstrap import INFO
from ttkbootstrap.style import Bootstyle

from static.constants import IMG_PATH_COLLAPSING as IMG_PATH


class CollapsingFrame(ttk.Frame):
    """A collapsible frame widget that opens and closes with a click."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.cumulative_rows = 0

        # widget images
        self.images = [
            ttk.PhotoImage(file=IMG_PATH / "arrow__1_a.png"),
            ttk.PhotoImage(file=IMG_PATH / "arrow_2_b.png"),
        ]

    def add(self, child, title="", bootstyle=INFO, **kwargs):
        """Add a child to the collapsible frame

        Parameters:

            child (Frame):
                The child frame to add to the widget.

            title (str):
                The title appearing on the collapsible section header.

            bootstyle (str):
                The style to apply to the collapsible section header.

            **kwargs (Dict):
                Other optional keyword arguments.
        """
        if child.winfo_class() != "TFrame":
            return

        style_color = Bootstyle.ttkstyle_widget_color(bootstyle)
        frm = ttk.Frame(self, bootstyle=style_color)
        frm.grid(row=self.cumulative_rows, column=0, sticky=ttk.EW)

        # header title
        header = ttk.Label(
            master=frm,
            text=title,
            bootstyle=(style_color, ttk.INVERSE),
            font=("Arial", 20),
        )
        if kwargs.get("textvariable"):
            header.configure(textvariable=kwargs.get("textvariable"))
        header.pack(side=ttk.LEFT, fill=ttk.BOTH, padx=10)

        # header toggle button
        def _func(c=child):
            return self._toggle_open_close(c)

        btn = ttk.Button(
            master=frm, image=self.images[0], bootstyle=style_color, command=_func
        )
        btn.pack(side=ttk.RIGHT)

        # assign toggle button to child so that it can be toggled
        child.btn = btn
        child.grid(row=self.cumulative_rows + 1, column=0, sticky="nswe")

        # increment the row assignment
        self.cumulative_rows += 2

    def _toggle_open_close(self, child):
        """Open or close the section and change the toggle button
        image accordingly.

        Parameters:

            child (Frame):
                The child element to add or remove from grid manager.
        """
        if child.winfo_viewable():
            child.grid_remove()
            child.btn.configure(image=self.images[1])
        else:
            child.grid()
            child.btn.configure(image=self.images[0])
