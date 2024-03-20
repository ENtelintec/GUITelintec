from templates.database.connection import connectionDB as db


class Customer:
    def __init__(self):
        self.connection = None
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

    def create_customer(self, name, email, phone, rfc, address):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            name = str(name)
            email = str(email)
            phone = str(phone)
            rfc = str(rfc)
            address = str(address)
            search_sql = "SELECT * FROM customers_amc WHERE name = %s"
            insert_sql = "INSERT INTO customers_amc (name, email, phone, rfc, address) VALUES (%s, %s, %s, %s, %s)"
            self.cursor.execute(search_sql, (name,))
            result = self.cursor.fetchone()
            if result:
                return "Customer already exists"
            self.cursor.execute(insert_sql, (name, email, phone, rfc, address))
            self.connection.commit()
            return True
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
            name = str(name)
            email = str(email)
            phone = str(phone)
            rfc = str(rfc)
            address = str(address)
            update_sql = "UPDATE customers_amc SET name = %s, email = %s, phone = %s, rfc = %s, address = %s WHERE id_customer = %s"
            self.cursor.execute(
                update_sql, (name, email, phone, rfc, address, id_customer)
            )
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
            delete_sql = "DELETE FROM customers_amc WHERE id_customer = %s"
            self.cursor.execute(delete_sql, (id_customer,))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None
