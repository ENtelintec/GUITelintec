import tkinter as tk

import customtkinter as ctk


# Define las listas de chats


class ChatsDisplay(ctk.CTkFrame):
    def __init__(self, master, chat, **kwargs):
        super().__init__(master,**kwargs)
        if chat is None:
            chat = []
        else:
            chat = chat
        self.chat = chat
 
        # Chat unificado:
        self.unificado = tk.Text(master, font=("Helvetica", 12))
        self.unificado.config(bg="#040530")
        self.unificado.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
       
        # self.unificado.grid_columnconfigure(0,weight=1)
        # self.unificado.grid_rowconfigure(0, weight=1)              

        for mensaje in self.chat:
            content = mensaje["content"]
            role = mensaje["role"]

            if role == "user":
                # Agregar un tag "user" para la alineación a la derecha
                # self.unificado.tag_add("user", "1.0", "1.4")
                self.unificado.tag_configure("user", justify="left",
                                             foreground="white",
                                             font=("Helvetica", 12, "bold"))
                self.unificado.insert(tk.END,
                                      f'USER: {content}\n',
                                      "user")
                self.unificado.insert(ctk.END, "\n")
            elif role == "assistant":
                # Agregar un tag "assistant" para la alineación a la izquierda
                # self.unificado.tag_add("assistant", "1.0", "1.4")
                self.unificado.tag_configure("assistant", justify="left",
                                             foreground="#0859ff",
                                             font=("Helvetica", 12, "bold"))
                self.unificado.insert(tk.END,
                                      f'Asistente: {content}\n',
                                      "assistant")
                self.unificado.insert(ctk.END, "\n")


# if __name__ == "__main__":
#     root = tk.Tk()
#     root.geometry("500x500")
#     chat = [{"content": "Hola", "role": "user"}, {"content": "Hola", "role": "assistant"}]
#     chat_display = ChatsDisplay(root, chat)
#     chat_display.pack(fill="both", expand=True)
#     root.mainloop()
