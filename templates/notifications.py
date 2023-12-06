import customtkinter as ctk
import ttkbootstrap as ttk
from CTkTable import *


def Reverse(lst):
    new_lst = lst[::-1]
    return new_lst


def read_file(filepath) -> list[tuple]:
    """
    Read the file and return a list of tuples with the data of the file.
    :return: list of tuples with the data of the file.
    :rtype: list of tuples.
    """
    out = []
    with open(filepath, 'r') as file:
        content = file.readlines()
        for item in content:
            out.append(tuple(item.split(',;')))
    return out


class Notifications(ttk.Frame):
    def __init__(self, master, data=None, filepath='../notifications.txt'):
        super().__init__(master)
        self.filepath = filepath
        self.counter_queue = 0
        self.handled_queue = 0
        self.queue_notifications = []
        self.data = read_file(self.filepath) if data is None else data

        # change the data initial for a read file.
        self.notifications_complete = [
            key for key in self.data if int(key[2]) == 1]
        self.notifications_complete = Reverse(self.notifications_complete)
        self.notifications_complete.insert(0, ('ID', 'Message', 'Status', 'Products', 'Timestamp'))
        self.notifications_pending = [
            key for key in self.data if int(key[2]) == 0]

        # scrollable frame for notifications
        self.note_frame = ctk.CTkScrollableFrame(master=self,
                                                 width=1100, height=550,
                                                 fg_color="#040546")
        self.note_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew", columnspan=6)
        self.note_frame.grid_columnconfigure(1, weight=1)
        self.note_frame.grid_rowconfigure(0, weight=1)

        if self.notifications_pending == []:
            self.value_pending = 0
        else:
            self.notifications_pending = Reverse(self.notifications_pending)
            self.notifications_pending.insert(0, ('ID', 'Message', 'Status', 'Products', 'Timestamp'))
            # Create a table to show all history of notifications
            self.table_pending = CTkTable(master=self.note_frame,
                                          row=len(self.notifications_pending),
                                          column=len(
                                              self.notifications_pending[0]),
                                          values=self.notifications_pending)
            self.table_pending.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", columnspan=len(
                self.notifications_complete[0]))
            self.table_pending.configure(wraplength=350, row=len(
                self.notifications_pending))
            self.value_pending = len(self.notifications_pending) - 1

            for index, item in enumerate(self.notifications_pending):
                if index != 0:
                    id, message, status, products, timestamp = item
                    button = ctk.CTkButton(master=self.table_pending, text="Revisar",
                                           command=lambda id=id: self.handle_notification(id))
                    button.grid(row=index, column=5, padx=10, pady=10, sticky="nsew")
            # Create a button to update the notifications
            self.update_button = ctk.CTkButton(
                master=self,
                text="Actualizar",
                command=self.update_all_status)
            self.update_button.grid(row=1, column=2, padx=10, pady=10, sticky="sw")
        # title label
        title_label = ctk.CTkLabel(master=self, text="Notificaciones",
                                   font=ctk.CTkFont(size=38, weight="bold"),
                                   text_color="#fff")
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="n", columnspan=6)
        # Create Widgets
        # Create a Counter text that shows the number of pending notifications
        self.pending_count = ctk.CTkLabel(
            master=self,
            text=f"Pendientes: {self.value_pending}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#fff")

        self.pending_count.grid(row=1, column=0, padx=10, pady=10, sticky="sw")

        self.value_complete = len(self.notifications_complete) - 1
        self.complete_count = ctk.CTkLabel(
            master=self,
            text=f"Revisadas: {self.value_complete}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#fff")
        self.complete_count.grid(row=1, column=1, padx=10, pady=10, sticky="sw")
        # Create a table to show all history of notifications
        self.table_complete = CTkTable(master=self.note_frame,
                                       row=len(self.notifications_complete),
                                       column=len(
                                           self.notifications_complete[0]),
                                       values=self.notifications_complete)
        self.table_complete.grid(row=2, column=0, padx=10, pady=10, sticky="nsew", columnspan=len(
            self.notifications_complete[0]))
        self.table_complete.configure(wraplength=350, row=len(
            self.notifications_pending))

    def handle_notification(self, id):
        new_data = []
        for item in (list(self.data)):
            id_, message, status, *products, timestamp = item
            if id_ == id:
                item_updated = (id_, message, 1, *products, timestamp)
            else:
                item_updated = item
            new_data.append(item_updated)
        self.data = new_data
        # override file notifications with new data
        for index, item in enumerate(self.data):
            id_, message, status, products, timestamp = item
            self.data[index] = f"{id_},;{message},;{status},;{products},;{timestamp}"
        with open(self.filepath, 'w') as file:
            file.writelines(self.data)

        # update the frame
        self.update_notifications_frame()

    def update_notifications_frame(self):
        """
        Update the frame with the new data.
        :return: None.
        :rtype: None.
        """

        self.table_pending.destroy()
        self.table_complete.destroy()
        self.pending_count.destroy()
        self.complete_count.destroy()
        self.update_button.destroy()

        self.data = read_file(self.filepath)
        self.notifications_complete = [
            key for key in self.data if int(key[2]) == 1]
        self.notifications_complete = Reverse(self.notifications_complete)
        self.notifications_complete.insert(0, ('ID', 'Message', 'Status', 'Products', 'Timestamp'))

        self.notifications_pending = [
            key for key in self.data if int(key[2]) == 0]

        if self.notifications_pending == []:
            self.value_pending = 0
            self.table_pending.destroy()
        else:
            self.notifications_pending = Reverse(self.notifications_pending)
            self.notifications_pending.insert(0, ('ID', 'Message', 'Status', 'Products', 'Timestamp'))
            self.value_pending = len(self.notifications_pending) - 1
            # Create a table to show all history of notifications
            self.table_pending = CTkTable(master=self.note_frame,
                                          row=len(self.notifications_pending),
                                          column=len(
                                              self.notifications_pending[0]),
                                          values=self.notifications_pending)
            self.table_pending.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", columnspan=len(
                self.notifications_complete[0]))
            self.table_pending.configure(wraplength=350, row=len(
                self.notifications_pending))
            for index, item in enumerate(self.notifications_pending):
                if index != 0:
                    id, message, status, products, timestamp = item
                    button = ctk.CTkButton(master=self.table_pending, text="Revisar",
                                           command=lambda id=id: self.handle_notification(id))
                    button.grid(row=index, column=5, padx=10, pady=10, sticky="nsew")
            # Create a button to update the notifications
            self.update_button = ctk.CTkButton(
                master=self,
                text="Actualizar",
                command=self.update_all_status)
            self.update_button.grid(row=1, column=2, padx=10, pady=10, sticky="sw")
        self.value_complete = len(self.notifications_complete) - 1
        # Create a table to show all history of notifications
        self.table_complete = CTkTable(master=self.note_frame,
                                       row=len(self.notifications_complete),
                                       column=len(
                                           self.notifications_complete[0]),
                                       values=self.notifications_complete)
        self.table_complete.grid(row=2, column=0, padx=10, pady=10, sticky="nsew", columnspan=len(
            self.notifications_complete[0]))
        self.table_complete.configure(wraplength=350, row=len(self.notifications_pending))

        self.pending_count = ctk.CTkLabel(
            master=self,
            text=f"Pendientes: {self.value_pending}",
            font=ctk.CTkFont(size=18, weight="bold"))

        self.pending_count.grid(row=1, column=0, padx=10, pady=10, sticky="sw")

        self.value_complete = len(self.notifications_complete) - 1
        self.complete_count = ctk.CTkLabel(
            master=self,
            text=f"Revisadas: {self.value_complete}",
            font=ctk.CTkFont(size=18, weight="bold"))

        self.complete_count.grid(row=1, column=1, padx=10, pady=10, sticky="sw")

    def update_all_status(self):
        new_data = []
        for item in (list(self.data)):
            id, message, status, *products, timestamp = item
            if status.strip() == '0':
                item_updated = (id, message, 1, *products, timestamp)
            else:
                item_updated = item
            new_data.append(item_updated)
        self.data = new_data

        # override file notifications with new data
        for index, item in enumerate(self.data):
            id, message, status, products, timestamp = item
            self.data[index] = f"{id},;{message},;{status},;{products},;{timestamp}"
        with open(self.filepath, 'w') as file:
            file.writelines(self.data)

        # update the frame
        self.update_notifications_frame()
