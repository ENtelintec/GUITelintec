import pandas as pd
import tkinter as tk

# from tkinter import  filedialog
from tkinter.filedialog import askopenfilename
from ttkbootstrap import *
import ttkbootstrap as ttk
from ttkbootstrap import Style
import customtkinter as ctk
from ttkbootstrap.tableview import Tableview
import templates.FunctionsSQL as cb
import json
import time
from datetime import datetime
class ManejoDatos(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.columnconfigure((0, 1, 2), weight=1)
        self.df = None
        self.file_selected = False
        self.master = None
        self.permissions = None
        self.data_for_tableview=None

        # -------------------create title-----------------
        self.label_title = ttk.Label(
            self, text="Telintec", font=("Helvetica", 32, "bold")
        )
        self.label_title.grid(row=0, column=0, columnspan=3)
        # -------------------create entry for file selector-----------------
        self.label_file = ttk.Label(self, text="File: ")
        self.label_file.grid(row=1, column=0)
        self.file_entry = ttk.Button(
            self, text="Seleccione un archivo", command=self.browse_file
        )
        self.file_entry.grid(row=1, column=1)
        self.label_filename = ttk.Label(self, text="")
        self.label_filename.grid(row=1, column=2)
        # -------------------create tableview for data-----------------
        self.table = Tableview(self)
        #  ------------------insert in DATA BASE-----------------------
        self.btnInsertDb = ttk.Button(
            self, text="Insertar en BD", command=self.insertarBd
        )
        # command=self.show_data
        self.btnInsertDb.grid(row=3, column=1)
        self.unif=ttk.Button(self, text='unificar datos', command=self.unificar_datos)
        self.unif.grid(row=4, column=1)
        # -------------------create tableview for grouped data-----------------
        self.grouped_table = Tableview(self)
        self.grouped_table.grid(
            row=5, column=0, columnspan=3, sticky="nsew", padx=20, pady=10
        )

        self.label_consul=ttk.Label(self, text="Empleados activos : ")
        self.label_consul.grid(row=6, column=0)

        self.btnShowStatus=ttk.Button(self, text="Mostrar empleados activos", command=self.emp_activos)
        self.btnShowStatus.grid(row=6, column=1)
                # Configurar el Treeview para mostrar los resultados
        columns = ('ID', 'Nombre', 'Blood', 'status',)
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.grid(row=7, column=0)




    def browse_file(self):
        try:
            filename = askopenfilename(
                filetypes=[("Excel Files", "*.xlsx"), ("Excel Files", "*.xls")]
            )
            print("Archivo: ", filename)
        except Exception as e:
            filename = e
        self.label_filename.configure(text=filename)
        self.file_entry.configure(text="File Selected")
        if ".xls" in filename or ".xlsx" in filename:
      
            self.df = pd.read_excel(filename)
            self.df= self.df.replace({pd.NaT:None})
            self.df.fillna("", inplace=True)
            
            # borrar valores vacios
            # print(self.df.head().to_string())

            coldata = []
            for i, col in enumerate(self.df.columns.tolist()):
                coldata.append({"text": col, "stretch": True})
            # print(coldata)
            self.table = Tableview(
                self,
                bootstyle="primary",
                coldata=coldata,
                rowdata=self.df.values.tolist(),
                paginated=False,
                searchable=True,
            )
            self.table.grid(
                row=2, column=0, columnspan=3, sticky="nsew", padx=20, pady=10
            )
         
    def unificar_datos(self):
     if self.df is not None:

        dict_employees = {}
        exams = []
        aptitudes = []
        status = None
        names = None
        blood = None
        empleado_id=None

        for i, col in enumerate(self.df.columns.tolist()):
            if i == 0:
                names = self.df[col].unique().tolist()
            elif i == 1:
                status = self.df[col].tolist()
            elif i == 2:
                blood = self.df[col].tolist()
            elif i == 3:
                exams.append(self.df[col].tolist())
            elif i == 4:
                aptitudes.append(self.df[col].tolist())
            elif i > 4:
                if i % 2 == 1:
                    exams.append(self.df[col].tolist())
                elif i % 2 == 0:
                    aptitudes.append(self.df[col].tolist())
        for i, name in enumerate(names):
            aptitud_emp=[]
            fechas_exam_emp=[]
            last_aptitud = None
            last_fecha_exam = None
            frst_fecha_exam = None
            # iteramos examenes
            for j, exam_list in enumerate(exams):
                fechas_exam_emp.append(exam_list[i])
            for j , apt in enumerate(aptitudes):
                aptitud_emp.append(apt[i])
            # buscar ulitma aptitud no nula
            for apt in aptitud_emp:
                if apt != '':
                    last_aptitud = apt
                else:  
                    break
            # Buscar la ultima fecha de examen no nula
            # Buscar la ultima fecha de examen no nula
            for exam in fechas_exam_emp:
                if isinstance(exam, pd.Timestamp):  # Verificar si exam es un Timestamp de Pandas
                    last_fecha_exam = exam.to_pydatetime()
                elif exam != '':
                    last_fecha_exam = datetime.strptime(str(exam), "%Y-%m-%d %H:%M:%S")
                else:
                    break
            
            # print(last_fecha_exam)
            
            # Buscar la primera fecha no nula de examen
            for exam in fechas_exam_emp:
                if isinstance(exam, pd.Timestamp):  # Verificar si exam es un Timestamp de Pandas
                    first_fecha_exam = exam.to_pydatetime()
                elif exam != '':
                    first_fecha_exam = datetime.strptime(str(exam), "%Y-%m-%d %H:%M:%S")
                    break
                
            print("Primera fecha de examen")
            print(first_fecha_exam)
                
                
            dict_employees[name] = {"status": status[i], "blood": blood[i],
                                    "exams": fechas_exam_emp,
                                    "aptitudes": aptitud_emp,
                                    "aptitud_actual": last_aptitud,
                                    "fecha_ultima_renovacion": last_fecha_exam,
                                    "empleado_id": empleado_id}

        print("------------------")
        # # print(dict_employees)
       
        # for c, (k, v) in enumerate(dict_employees.items()):
        #         print(f"Empleado {c + 1}: {k}")
        #         print(f"  Aptitudes:")
        #         for index, aptitud in enumerate(v["aptitudes"]):
        #             print(f" APTITUD{index + 1 }: {aptitud}")
        #         print(f"Examenes fecha: ")
        #         for index, examen in enumerate(v["exams"]): 
        #             print(f" EXAMEN{index + 1 }: {examen}")
                
        #         print()
       

        print("------------------")
       
       # Mapeo para convertir abreviaturas a palabras completas
        status_mapping = {"A": "Activo", "I": "Inactivo"}
        # Crear un nuevo diccionario para almacenar los datos en la forma deseada
        data_for_tableview = {"EMPLEADOS": [], "STATUS": [], "BLOOD": [], "APTITUD": [], "RENOVACION": [],"APTITUD_ACTUAL": [],  "FECHA_ULTIMA_RENOVACION":[], "EMPLEADO_ID": []}
        # Llenar el nuevo diccionario con datos de dict_employees
        for empleado, data in dict_employees.items():
            data_for_tableview["EMPLEADOS"].append(empleado)
            data_for_tableview["STATUS"].append(status_mapping.get(data["status"][0], ""))  # Mostrar el primer elemento de la lista, o cadena vacía si está vacía
            data_for_tableview["BLOOD"].append(data["blood"][:2] if data["blood"] else "")  # Mostrar el primer elemento de la lista, o cadena vacía si está vacía
            data_for_tableview["APTITUD"].append(str(data["aptitudes"]))
            data_for_tableview["RENOVACION"].append(str(data["exams"]))
            data_for_tableview["APTITUD_ACTUAL"].append(data["aptitud_actual"])  
            data_for_tableview["FECHA_ULTIMA_RENOVACION"].append(data[ "fecha_ultima_renovacion"])  
            data_for_tableview["EMPLEADO_ID"].append(data["empleado_id"])  


        self.grouped_table.destroy()
        self.data_for_tableview=data_for_tableview
        self.grouped_table = Tableview(self, bootstyle="primary", coldata=[
                {"text": "EMPLEADOS", "stretch": True},
                {"text": "STATUS", "stretch": True},
                {"text": "BLOOD", "stretch": True},
                {"text": "APTITUD", "stretch": True},
                {"text": "RENOVACION", "stretch": True},
                {"text": "APTITUD_ACTUAL", "stretch": True},  
                {"text": "FECHA_ULTIMA_RENOVACION", "stretch": True},  
                {"text": "EMPLEADO_ID", "stretch": True}  # Nueva columna para empleados_id
            ], rowdata=list(zip(data_for_tableview["EMPLEADOS"], data_for_tableview["STATUS"], data_for_tableview["BLOOD"] , data_for_tableview["APTITUD"], data_for_tableview["RENOVACION"],data_for_tableview["APTITUD_ACTUAL"],data_for_tableview["FECHA_ULTIMA_RENOVACION"],
                            data_for_tableview["EMPLEADO_ID"])))
        self.grouped_table.grid(row=5, column=0, columnspan=3, sticky='nsew', padx=20, pady=10)
    
    def insertarBd(self):
        if self.data_for_tableview is not None:
        # Crear la tabla en la base de datos
            # create_table_sql = ("CREATE TABLE IF NOT EXISTS examenes_med (examen_id INT AUTO_INCREMENT PRIMARY KEY,"
            #                     " nombre VARCHAR(255),"
            #                     " blood VARCHAR(255),"
            #                      "status VARCHAR(255), "
            #                      "aptitud JSON,"
            #                     " renovacion JSON)"
            #                     "PRIMARY KEY(examen_id)"
            #                     "foreign key (empleado_id) references employees (employee_id) on update restrict"
            #                     "foreign key (aptitud) references aptitude (aptitude_id) on update restrict")
                                
        # Ejecutar la creación de la tabla

            # flag, error , result =cb.execute_sql(create_table_sql, type_sql=3)
            # print(flag, error,result)
        # Insertar datos en la tabla
         for  status, blood,empleado, aptitud,renovacion,aptitude_actual,fecha_ultima_renovacion,empleado_id in zip(
            self.data_for_tableview["STATUS"],
            self.data_for_tableview["BLOOD"],
            self.data_for_tableview["EMPLEADOS"],
            self.data_for_tableview["APTITUD"],
            self.data_for_tableview["RENOVACION"],
            self.data_for_tableview["APTITUD_ACTUAL"],
            self.data_for_tableview["FECHA_ULTIMA_RENOVACION"],
            self.data_for_tableview["EMPLEADO_ID"],

        ):
            # result=cb.get_id_employee(empleado)
            # if  len(result)==0:
            
            if "Inactivo" in status:
                result=60
            else:
                result=cb.get_id_employee(empleado)
                if len(result)==0:
                    print(result,empleado)
                    continue
               
                result=result[0] 
            
            insert_sql = ( "INSERT INTO  examenes_med ( name ,status, blood, aptitud, renovacion, aptitude_actual, fecha_ultima_renovacion,empleado_id)"
                           "VALUES (%s, %s, %s, %s, %s,%s,%s,%s)")
            values = (empleado, status, blood, json.dumps(aptitud), json.dumps(renovacion),aptitude_actual,  # Accede al primer elemento o utiliza None si la lista está vacía
            fecha_ultima_renovacion,  # Accede al primer elemento o utiliza None si la lista está vacía
            result)
          
            # Ejecutar la inserción de datos
            flag, error , result=cb.execute_sql(insert_sql, values, type_sql=3)
            print(flag, error,result)
            time.sleep(0.1)
        else:
            print("Error: data_for_tableview no ha sido inicializado en unificar_datos.")
    
    def emp_activos(self):
         # Limpiar resultados anteriores en el Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Realizar la consulta a la base de datos
        query = "SELECT * FROM sql_telintec.examenes_med WHERE status ='Activo';"
        flag, error , result=cb.execute_sql(query, type_sql=2)
        # self.cursor.execute(query)
        # resultados = self.cursor.fetchall()

        # Mostrar los resultados en el Treeview
        for result in result:
            self.tree.insert('', 'end', values=result)


       
          
    

       

                    
if __name__ == "__main__":
    app = ManejoDatos()
    style = Style(theme="minty")
    app.pack(expand=tk.YES, fill=tk.BOTH)
    app.mainloop()
