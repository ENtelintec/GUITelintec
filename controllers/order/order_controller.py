from database.connection import connectionDB as db
from templates.FunctionsSQL import execute_sql


class Order:
    def __init__(self):
        self.connection = db()
        self.cursor = self.connection.cursor()

    def get_profit(self):
        sql = """
        SELECT SUM(order_details_amc.quantity * products_amc.price) AS profit
        FROM orders_amc JOIN order_details_amc ON orders_amc.id_order = order_details_amc.id_order
        JOIN products_amc ON order_details_amc.id_product = products_amc.id_product;"""
        try:
            # self.cursor.execute(sql)
            result = execute_sql(sql, (), 5)
            # result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'

    def get_all_orders(self):
        sql = """
        SELECT orders_amc.id_order, orders_amc.date, orders_amc.return_status, 
        customers_amc.name AS customer_name, customer_addresses_amc.address AS customer_address,
        customer_addresses_amc.city AS customer_city, customer_addresses_amc.postal_code AS customer_postal_code,
        order_details_amc.id_order_detail, order_details_amc.quantity, products_amc.id_product, products_amc.name AS product_name
        FROM orders_amc JOIN customers_amc ON orders_amc.id_customer = customers_amc.id_customer
        LEFT JOIN customer_addresses_amc ON orders_amc.id_customer = customer_addresses_amc.id_customer
        LEFT JOIN order_details_amc ON orders_amc.id_order = order_details_amc.id_order
        LEFT JOIN products_amc ON order_details_amc.id_product = products_amc.id_product;"""
        # LEFT JOIN product_movements ON products.id_product = product_movements.id_product;
        try:
            # self.cursor.execute(sql)
            # result = self.cursor.fetchall()
            result = execute_sql(sql, (), 5)
            return result
        except Exception as e:
            return f'Error: {e}'

    def get_single_order(self, id_order):
        try:
            self.cursor.execute(
                f"SELECT * FROM orders WHERE id = {id_order}")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'

    def update_order(self, id_order, id_customer, return_status, id_order_detail, id_product, quantity):
        try:
            sql = (f"UPDATE orders SET id_customer = {id_customer}, return_status = '{return_status}' "
                   f"WHERE id_order = {id_order}")
            self.cursor.execute(sql)
            self.connection.commit()
            sql2 = (f"UPDATE order_details SET id_product = {id_product}, quantity = {quantity} "
                    f"WHERE id_order_detail = {id_order_detail}")
            self.cursor.execute(sql2)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def delete_order(self, id_order):
        try:
            sql = f"DELETE FROM order_details WHERE id_order = {id_order}"
            self.cursor.execute(sql)
            self.connection.commit()
            sql2 = f"DELETE FROM orders WHERE id_order = {id_order}"
            self.cursor.execute(sql2)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def close_connection(self):
        self.connection.close()
        self.cursor.close()