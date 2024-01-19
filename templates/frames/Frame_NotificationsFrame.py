import customtkinter as ctk
import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview


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
    def __init__(self, master, data=None, filepath='files/notifications.txt'):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.filepath = filepath
        self.counter_queue = 0
        self.handled_queue = 0
        self.queue_notifications = []
        self.data = read_file(self.filepath) if data is None else data
        # title label
        title_label = ttk.Label(self, text="Notificaciones",
                                font=("Helvetica", 32, "bold"))
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="n", columnspan=3)
        # change the data initial for a read file.
        self.notifications_complete = [
            key for key in self.data if int(key[2]) == 1]
        self.notifications_complete = Reverse(self.notifications_complete)
        self.notifications_pending = [
            key for key in self.data if int(key[2]) == 0]
        if len(self.notifications_pending) == 0:
            self.value_pending = 0
        else:
            self.notifications_pending = Reverse(self.notifications_pending)
            self.notifications_pending.insert(0, ('ID', 'Message', 'Status', 'Products', 'Timestamp'))
            # Create a table to show all history of notifications
            self.table_pending = Tableview(
                self,
                coldata=['ID', 'Message', 'Status', 'Products', 'Timestamp'],
                rowdata=self.notifications_pending,
                paginated=False,
                searchable=True,
                bootstyle="danger"
                )
            self.table_pending.grid(row=2, column=0, padx=30, pady=10, sticky="nsew",
                                    columnspan=3)
            self.table_pending.view.bind("<Double-1>", self.handle_notification)
            self.value_pending = len(self.notifications_pending) - 1

            # Create a button to update the notifications
            self.update_button = ctk.CTkButton(self,
                                               text="Actualizar",
                                               command=self.update_all_status)
            self.update_button.grid(row=1, column=2, padx=10, pady=10, sticky="sw")
        # Create a Counter text that shows the number of pending notifications
        self.pending_count = ttk.Label(
            self,
            text=f"Pendientes: {self.value_pending}",
            font=("Helvetica", 18, "normal")
        )
        self.pending_count.grid(row=1, column=0, padx=10, pady=10, sticky="sw")

        self.value_complete = len(self.notifications_complete) - 1
        self.complete_count = ttk.Label(
            master=self,
            text=f"Revisadas: {self.value_complete}",
            font=("Helvetica", 18, "normal"))
        self.complete_count.grid(row=1, column=1, padx=10, pady=10, sticky="sw")
        # Create a table to show all history of notifications
        self.table_complete = Tableview(
            self,
            coldata=['ID', 'Message', 'Status', 'Products', 'Timestamp'],
            rowdata=self.notifications_complete,
            paginated=False,
            searchable=True,
            bootstyle="info"
        )
        self.table_complete.grid(
            row=3, column=0, padx=30, pady=10, sticky="nsew", columnspan=3
        )

    def handle_notification(self, event):
        (id_not, message, status, products, timestamp) = self.table_pending.view.item(
            event.widget.selection()[0], "values")
        new_data = []
        for item in (list(self.data)):
            id_, message, status, *products, timestamp = item
            if id_ == id_not:
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
        self.notifications_pending = [
            key for key in self.data if int(key[2]) == 0]
        if len(self.notifications_pending) == 0:
            self.value_pending = 0
            self.table_pending.destroy()
        else:
            self.notifications_pending = Reverse(self.notifications_pending)
            self.notifications_pending.insert(0, ('ID', 'Message', 'Status', 'Products', 'Timestamp'))
            self.value_pending = len(self.notifications_pending) - 1
            # Create a table to show all history of notifications
            self.table_pending = Tableview(
                self,
                coldata=['ID', 'Message', 'Status', 'Products', 'Timestamp'],
                rowdata=self.notifications_pending,
                paginated=False,
                searchable=True,
                bootstyle="warning"
            )
            self.table_pending.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
            self.table_pending.view.bind("<Double-1>", self.handle_notification)
            self.update_button = ttk.Button(
                master=self,
                text="Actualizar",
                command=self.update_all_status)
            self.update_button.grid(row=1, column=2, padx=10, pady=10, sticky="sw")
        self.value_complete = len(self.notifications_complete) - 1
        # Create a table to show all history of notifications
        self.table_complete = Tableview(
            self,
            coldata=['ID', 'Message', 'Status', 'Products', 'Timestamp'],
            rowdata=self.notifications_complete,
            paginated=False,
            searchable=True
        )
        self.table_complete.grid(row=3, column=0, padx=30, pady=10, sticky="nsew")
        self.pending_count = ttk.Label(
            master=self,
            text=f"Pendientes: {self.value_pending}",
            font=("Helvetica", 18, "normal"))
        self.pending_count.grid(row=1, column=0, padx=10, pady=10, sticky="sw")
        self.value_complete = len(self.notifications_complete) - 1
        self.complete_count = ttk.Label(
            master=self,
            text=f"Revisadas: {self.value_complete}",
            font=("Helvetica", 18, "normal"))
        self.complete_count.grid(row=1, column=1, padx=10, pady=10, sticky="sw")

    def update_all_status(self):
        new_data = []
        for item in (list(self.data)):
            id_not, message, status, *products, timestamp = item
            if status.strip() == '0':
                item_updated = (id_not, message, 1, *products, timestamp)
            else:
                item_updated = item
            new_data.append(item_updated)
        self.data = new_data

        # override file notifications with new data
        for index, item in enumerate(self.data):
            id_not, message, status, products, timestamp = item
            self.data[index] = f"{id_not},;{message},;{status},;{products},;{timestamp}"
        with open(self.filepath, 'w') as file:
            file.writelines(self.data)

        # update the frame
        self.update_notifications_frame()
