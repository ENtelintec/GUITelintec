
import tkinter as tk
from tkinter import ttk 
import customtkinter as ctk


class VisualPedidos(ttk.Treeview):
    def __init__(self,master, **kwargs):
        super().__init__(master,**kwargs)
        # tk.Frame.__init__(self, master, **kwargs)
        # Crear el Treeview
        self.tree = ttk.Treeview(self, columns=("Nombre", "Edad"))
        self.tree.heading("#1", text="Nombre")
        self.tree.heading("#2", text="Edad")

        # Agregar algunos datos ficticios
        self.tree.insert("", "end", values=("Juan", 30))
        self.tree.insert("", "end", values=("María", 25))
        self.tree.insert("", "end", values=("Carlos", 35))
        self.tree.insert("", "end", values=("Laura", 28))

        # self.tree.pack()

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = VisualPedidos(root)
#     root.mainloop()
