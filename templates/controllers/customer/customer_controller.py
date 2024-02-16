from templates.database.connection import connectionDB as db


class Customer:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def create_customer(self, name, email, phone, rfc, address):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql1 = f"INSERT INTO customers_amc (name, email, phone, rfc, address) VALUES ('{name}', '{email}', '{phone}', '{rfc}', '{address}')"
            self.cursor.execute(sql1)
            id_customer = self.cursor.lastrowid
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_all_customers(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"SELECT * FROM customers_amc"
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def update_customer(self, id_customer, name, email, phone, rfc, address):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql1 = f"UPDATE customers_amc SET name = '{name}', email = '{email}', phone = '{phone}', rfc = '{rfc}', address = '{address}' WHERE id_customer = {id_customer}"
            self.cursor.execute(sql1)
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def delete_customer(self, id_customer):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM customers_amc WHERE id_customer = {id_customer}"
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
