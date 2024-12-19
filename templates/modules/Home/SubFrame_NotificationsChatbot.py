import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from templates.misc.Functions_Files import get_cache_notifications
from templates.Functions_GUI_Utils import create_label, Reverse


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


def get_notifications_tables(data):
    complete = [key for key in data if int(key[1]) == 1]
    complete = Reverse(complete)
    pending = [key for key in data if int(key[1]) == 0]
    pending = Reverse(pending)
    return complete, pending


class NotificationsChatbot(ttk.Frame):
    def __init__(self, master, settings: dict = None, **kwargs):
        super().__init__(master)
        self.table_pending = None
        self.table_complete = None
        self.columnconfigure(0, weight=1)
        self.filepath = settings["chatbot"]["filepath"]
        self.filepath_cache = settings["chatbot"]["cache"]
        self.counter_queue = 0
        self.handled_queue = 0
        self.queue_notifications = []
        data_dic_chatbot = get_cache_notifications(self.filepath_cache)
        self.data = data_dic_chatbot["chatbot"]["data"]
        self.columns = data_dic_chatbot["chatbot"]["columns"]
        self.svar_pending = ttk.StringVar()
        self.svar_complete = ttk.StringVar()
        # ------------------------------title label------------------------
        title_label = ttk.Label(self, text="Notificaciones Chatbot",
                                font=("Helvetica", 22, "bold"))
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        # ------------------- change the data initial for a read file.-----------
        self.notifications_complete, self.notifications_pending = get_notifications_tables(self.data)
        self.svar_pending.set(f"Pendientes: {len(self.notifications_pending)}")
        self.svar_complete.set(f"Revisadas: {len(self.notifications_complete)}")
        # ---------------------------------widgets info-------------------------
        frame_info_widgets = ttk.Frame(self)
        frame_info_widgets.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        frame_info_widgets.columnconfigure((0, 1), weight=1)
        # Create a Counter text that shows the number of pending notifications
        create_label(frame_info_widgets, 0, 0, textvariable=self.svar_pending,
                     font=("Helvetica", 18, "normal"))
        create_label(frame_info_widgets, 0, 1, textvariable=self.svar_complete,
                     font=("Helvetica", 18, "normal"))
        # ----------------------------tables----------------------------------
        frame_tables = ttk.Frame(self)
        frame_tables.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        frame_tables.columnconfigure(0, weight=1)
        self.create_tables(frame_tables, data={"complete": self.notifications_complete, "pending": self.notifications_pending})

    def _on_pending_double_click(self, event):
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

        data_dic_chatbot = get_cache_notifications(self.filepath_cache)
        self.data = data_dic_chatbot["chatbot"]["data"]
        self.columns = data_dic_chatbot["chatbot"]["columns"]
        self.notifications_complete, self.notifications_pending = get_notifications_tables(
            self.data)
        self.svar_pending.set(f"Pendientes: {len(self.notifications_pending)}")
        self.svar_complete.set(f"Revisadas: {len(self.notifications_complete)}")
        self.create_tables(self, data={"complete": self.notifications_complete, "pending": self.notifications_pending})

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
    
    def create_tables(self, master, data):
        """
        Create a table with the data.
        :param master: The master of the table.
        :type master: ttk.Frame.
        :param data: The data to show in the table.
        :type data: list.
        :return: None.
        :rtype: None.
        """
        self.table_complete.destroy() if self.table_complete is not None else None
        self.table_pending.destroy() if self.table_pending is not None else None
        
        self.table_complete = Tableview(
            master,
            coldata=self.columns,
            rowdata=data["complete"],
            paginated=True,
            searchable=False,
            bootstyle="success",
            autofit=True,
            autoalign=True
        )
        self.table_complete.grid(row=1, column=0, padx=30, pady=10, sticky="n")
        self.table_pending = Tableview(
            master,
            coldata=self.columns,
            rowdata=data["pending"],
            paginated=True,
            searchable=False,
            bootstyle="warning",
            autofit=True,
            autoalign=True
        )
        self.table_pending.grid(row=0, column=0, padx=30, pady=10, sticky="n")

    def update_procedure(self, **events):
        self.update_notifications_frame()
