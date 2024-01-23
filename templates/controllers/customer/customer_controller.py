from templates.database.connection import connectionDB as db


class Customer:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def create_customer(self, name, email, phone, address, city, postal_code):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql1 = (
                f"INSERT INTO customers_amc (name, email, phone) "
                f"VALUES ('{name}', '{email}', '{phone}')"
            )
            self.cursor.execute(sql1)
            id_customer = self.cursor.lastrowid
            self.connection.commit()

            sql2 = (
                f"INSERT INTO customer_addresses_amc (id_customer, address, city, postal_code) "
                f"VALUES ('{id_customer}','{address}', '{city}', '{postal_code}')"
            )
            self.cursor.execute(sql2)
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
            sql = """SELECT customers_amc.id_customer, customers_amc.name AS customer_name, customers_amc.email, customers_amc.phone as customer_phone, customer_addresses_amc.address as customer_address,
                    customer_addresses_amc.city AS customer_city, customer_addresses_amc.postal_code AS customer_postal_code
                    FROM customers_amc
                    LEFT JOIN customer_addresses_amc ON customers_amc.id_customer = customer_addresses_amc.id_customer
                    """
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

    def get_single_customer(self, id_customer):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                f"SELECT * FROM customers_amc " f"WHERE id = {id_customer}"
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

    def update_customer(
        self, id_customer, name, email, phone, address, city, postal_code
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql1 = (
                f"UPDATE customers_amc "
                f"SET name = '{name}', email = '{email}', phone = '{phone}' "
                f"WHERE id_customer = {id_customer}"
            )
            self.cursor.execute(sql1)
            self.connection.commit()

            sql2 = (
                f"UPDATE customer_addresses_amc "
                f"SET address = '{address}', city = '{city}', postal_code = '{postal_code}' "
                f"WHERE id_customer = {id_customer}"
            )
            self.cursor.execute(sql2)
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
