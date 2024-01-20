from database.connection import connectionDB as db


class Supplier:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_all_suppliers(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute("SELECT * FROM suppliers_amc")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_single_supplier(self, id_supplier):
        try:
            self.cursor.execute(f"SELECT * FROM suppliers_amc WHERE id = {id_supplier}")
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def update_supplier(self, id_supplier, name, address, phone, email):
        try:
            sql = (
                f"UPDATE suppliers_amc SET name = '{name}', address = '{address}', phone = '{phone}', email = '{email}' "
                f"WHERE id = {id_supplier}"
            )
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def delete_supplier(self, id_supplier):
        try:
            sql = f"DELETE FROM suppliers_amc WHERE id = {id_supplier}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None
