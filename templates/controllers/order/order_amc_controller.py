from templates.database.connection import connectionDB as db

class Order:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.id_request = None

    def create_order(
        self,
        order_date,
        sm_code,
        contract,
        order_number,
        plant,
        ubication,
        requester,
        telintec_personal,
        delivery_date,
        filter_items,
        items,
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()

            insert_sql = "INSERT INTO orders_amc (id_customer, order_date, sm_code, contract, order_number, operation_plant, ubication, requester, personal, estimated_date, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            self.cursor.execute(
                insert_sql,
                (
                    None,
                    order_date,
                    sm_code,
                    contract,
                    order_number,
                    plant,
                    ubication,
                    requester,
                    telintec_personal,
                    delivery_date,
                    "Pending",
                ),
            )
            self.connection.commit()

            for i in range(len(filter_items)):
                fila = {key: values[i] for key, values in items.items()}
                product_id = fila[0]
                product_name = fila[1]
                quantity = fila[4]
                metric_unit = fila[5]
                description = fila[6]

                search_sql = "SELECT id_product FROM products_amc WHERE sku = %s"
                self.cursor.execute(search_sql, (product_id,))
                result = self.cursor.fetchone()
                if result:
                    product_id = result[0]
                    insert_sql = "fINSERT INTO order_details_amc (id_order, id_product, quantity,description) VALUES (%s, %s, %s, %s)"
                    self.cursor.execute(
                        insert_sql,
                        (
                            self.cursor.lastrowid,
                            product_id,
                            quantity,
                            description,
                        ),
                    )
                    self.connection.commit()
                else:
                    insert_sql = "INSERT INTO products_amc (sku, name, udm, stock, minStock, maxStock, reorderPoint, id_category) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    self.cursor.execute(
                        insert_sql,
                        (product_id, product_name, metric_unit, 0, 1, None, None, None),
                    )
                    self.connection.commit()
                    insert_sql = "INSERT INTO order_details_amc (id_order, id_product, quantity,description) VALUES (%s, %s, %s, %s)"
                    self.cursor.execute(
                        insert_sql,
                        (
                            self.cursor.lastrowid,
                            self.cursor.lastrowid,
                            quantity,
                            description,
                        ),
                    )
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
            sql = "SELECT * FROM get_all_orders"
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

    def create_sm(
        self,
        order_date,
        sm_code,
        contract,
        order_number,
        plant,
        ubication,
        requester,
        telintec_personal,
        delivery_date,
        filter_items,
        items,
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            insert_sql = "INSERT INTO movement_requests_amc (order_date, sm_code, contract, order_number, operation_plant, ubication, requester, personal, estimated_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

            self.cursor.execute(
                insert_sql,
                (
                    order_date,
                    sm_code,
                    contract,
                    order_number,
                    plant,
                    ubication,
                    requester,
                    telintec_personal,
                    delivery_date,
                ),
            )
            self.connection.commit()
            self.id_request = self.cursor.lastrowid

            for i in range(len(filter_items)):
                fila = {key: values[i] for key, values in items.items()}
                product_id = fila[0]
                product_name = fila[1]
                quantity = fila[4]
                metric_unit = fila[5]
                description = fila[6]
                # before inserting the product, we need to check if all the fields are filled, if not we need to fill them with None
                if type(description) == float:
                    description = None
                insert_sql = "INSERT INTO movement_request_details_amc (id_request,sku,name,quantity,unit, description) VALUES (%s, %s, %s, %s, %s, %s)"
                self.cursor.execute(
                    insert_sql,
                    (
                        self.id_request,
                        product_id,
                        product_name,
                        quantity,
                        metric_unit,
                        description,
                    ),
                )
                self.connection.commit()

        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_all_orders_sm(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = "SELECT * FROM get_all_movement_requests"
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

    def delete_order_sm(self, id_request):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            delete_details_sql = (
                "DELETE FROM movement_request_details_amc WHERE id_request = %s"
            )
            self.cursor.execute(delete_details_sql, (id_request,))
            self.connection.commit()

            delete_request_sql = (
                "DELETE FROM movement_requests_amc WHERE id_request = %s"
            )
            self.cursor.execute(delete_request_sql, (id_request,))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None
