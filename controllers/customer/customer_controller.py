from database.connection import connectionDB as db


class Customer:
    def __init__(self):
        self.connection = db()
        self.cursor = self.connection.cursor()

    def create_customer(self, name, email, phone, address, city, postal_code):
        try:
            sql1 = (f"INSERT INTO customers_amc (name, email, phone) "
                    f"VALUES ('{name}', '{email}', '{phone}')")
            self.cursor.execute(sql1)
            id_customer = self.cursor.lastrowid
            self.connection.commit()

            sql2 = (f"INSERT INTO customer_addresses_amc (id_customer, address, city, postal_code) "
                    f"VALUES ('{id_customer}','{address}', '{city}', '{postal_code}')")
            self.cursor.execute(sql2)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def get_all_customers(self):
        try:
            sql = ("SELECT customers_amc.id_customer, customers_amc.name AS customer_name,"
                   "customers_amc.email, customers_amc.address AS customer_address,"
                   "customer_addresses_amc.city AS customer_city, "
                   "customer_addresses_amc.postal_code AS customer_postal_code "
                   "FROM customers_amc LEFT JOIN customer_addresses_amc ON customers_amc.id_customer = customer_addresses_amc.id_customer")
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'

    def get_single_customer(self, id_customer):
        try:
            self.cursor.execute(
                f"SELECT * FROM customers "
                f"WHERE id = {id_customer}")
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            return f'Error: {e}'

    def update_customer(self, id_customer, name, email, phone, address, city, postal_code):
        try:
            sql1 = (f"UPDATE customers "
                    f"SET name = '{name}', email = '{email}', phone = '{phone}' "
                    f"WHERE id_customer = {id_customer}")
            self.cursor.execute(sql1)
            self.connection.commit()

            sql2 = (f"UPDATE customer_addresses "
                    f"SET address = '{address}', city = '{city}', postal_code = '{postal_code}' "
                    f"WHERE id_customer = {id_customer}")
            self.cursor.execute(sql2)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def delete_customer(self, id_customer):
        try:
            sql = f"DELETE FROM customers WHERE id_customer = {id_customer}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def close_connection(self):
        self.connection.close()
        self.cursor.close()
