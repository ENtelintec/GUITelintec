from templates.database.connection import connectionDB as db


class Order:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def create_order(self, id_customer, return_status, products_list):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"INSERT INTO orders_amc (id_customer, return_status) VALUES ({id_customer}, '{return_status}')"
            self.cursor.execute(sql)
            self.connection.commit()
            order_id = self.cursor.lastrowid

            for product in products_list:
                product_id = product[0].split()[0]
                product_quantity = product[1]
                sql2 = f"INSERT INTO order_details_amc (id_order, id_product, quantity) VALUES ({order_id}, {product_id}, {product_quantity})"
                self.cursor.execute(sql2)
                self.connection.commit()

        except Exception as e:
            return f"Error: {e}"

        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def update_order(
        self,
        id_order,
        id_customer,
        return_status,
        products_list,
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = (
                f"UPDATE orders_amc SET id_customer = {id_customer}, return_status = '{return_status}' "
                f"WHERE id_order = {id_order}"
            )
            self.cursor.execute(sql)
            self.connection.commit()
            for product in products_list:
                product_id = product[0].split()[0]
                product_quantity = product[1]
                sql2 = f"UPDATE order_details_amc SET id_product = {product_id}, quantity = {product_quantity} WHERE id_order_detail = {id_order}"
                self.cursor.execute(sql2)
                self.connection.commit()

        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_total_products(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = """
            SELECT SUM(order_details_amc.quantity) AS total_products
            FROM orders_amc JOIN order_details_amc ON orders_amc.id_order = order_details_amc.id_order;"""
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

    def get_profit(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = """
            SELECT SUM(order_details_amc.quantity * products_amc.price) AS profit
            FROM orders_amc JOIN order_details_amc ON orders_amc.id_order = order_details_amc.id_order
            JOIN products_amc ON order_details_amc.id_product = products_amc.id_product;"""
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

    def get_all_orders(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"SELECT * FROM get_all_orders"
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

    def delete_order(self, id_order):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM order_details_amc WHERE id_order_detail = {id_order}"
            self.cursor.execute(sql)
            self.connection.commit()
            sql2 = f"DELETE FROM orders_amc WHERE id_order = {id_order}"
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
