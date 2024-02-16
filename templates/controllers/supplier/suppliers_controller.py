from templates.database.connection import connectionDB as db


class Supplier:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_all_suppliers(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute("SELECT * FROM suppliers_amc;")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def create_supplier(
        self,
        name_provider,
        seller_provider,
        email_provider,
        phone_provider,
        address_provider,
        web_provider,
        type_provider,
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"INSERT INTO suppliers_amc (name, seller_name, seller_email, phone, address, web_url, type) VALUES ('{name_provider}', '{seller_provider}', '{email_provider}', '{phone_provider}', '{address_provider}', '{web_provider}', '{type_provider}')"
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

    def update_supplier(
        self,
        id_provider,
        name_provider,
        seller_provider,
        email_provider,
        phone_provider,
        address_provider,
        web_provider,
        type_provider,
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"UPDATE suppliers_amc SET name = '{name_provider}', seller_name = '{seller_provider}', seller_email = '{email_provider}', phone = '{phone_provider}', address = '{address_provider}', web_url = '{web_provider}', type = '{type_provider}' WHERE id_supplier = {id_provider}"
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
