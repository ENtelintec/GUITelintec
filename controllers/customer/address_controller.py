from database.connection import connectionDB as db


class Address:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_all_addresses(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute("SELECT * FROM customer_addresses_amc")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_single_address(self, id_address):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                f"SELECT * FROM customer_addresses_amc WHERE id = {id_address}"
            )
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def update_address(
        self, id_address, street, number, city, state, country, zip_code
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"UPDATE customer_addresses SET street = '{street}', number = '{number}', city = '{city}', state = '{state}', country = '{country}', zip_code = '{zip_code}' WHERE id = {id_address}"
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

    def delete_address(self, id_address):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM customer_addresses_amc WHERE id = {id_address}"
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
