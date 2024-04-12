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
            search_sql = "SELECT * FROM suppliers_amc WHERE name = %s"
            insert_sql = "INSERT INTO suppliers_amc (name, seller_name, seller_email, phone, address, web_url, type) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            self.cursor.execute(search_sql, (name_provider,))
            result = self.cursor.fetchone()
            name_provider = str(name_provider)
            seller_provider = str(seller_provider)
            email_provider = str(email_provider)
            phone_provider = str(phone_provider)
            address_provider = str(address_provider)
            web_provider = str(web_provider)
            type_provider = str(type_provider)
            if result:
                return "Supplier already exists"
            self.cursor.execute(
                insert_sql,
                (
                    name_provider,
                    seller_provider,
                    email_provider,
                    phone_provider,
                    address_provider,
                    web_provider,
                    type_provider,
                ),
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
            update_sql = "UPDATE suppliers_amc SET name = %s, seller_name = %s, seller_email = %s, phone = %s, address = %s, web_url = %s, type = %s WHERE id_supplier = %s"
            self.cursor.execute(
                update_sql,
                (
                    name_provider,
                    seller_provider,
                    email_provider,
                    phone_provider,
                    address_provider,
                    web_provider,
                    type_provider,
                    id_provider,
                ),
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

    def delete_supplier(self, id_supplier):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            delete_sql = "DELETE FROM suppliers_amc WHERE id_supplier = %s"
            self.cursor.execute(delete_sql, (id_supplier,))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None
