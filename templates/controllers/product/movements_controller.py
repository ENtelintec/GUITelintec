from templates.database.connection import connectionDB as db


class Movement:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_ins(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                """
                    SELECT product_movements_amc.*, products_amc.name as product_name
                    FROM product_movements_amc
                    JOIN products_amc ON product_movements_amc.id_product = products_amc.id_product
                    WHERE product_movements_amc.movement_type = 'entrada';
                """
            )
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def create_in_movement(self, id_product, movement_type, quantity, movement_date):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            search_sql = "SELECT * FROM product_movements_amc WHERE id_product = %s"
            insert_sql = (
                "INSERT INTO product_movements_amc (id_product, movement_type, quantity, movement_date) "
                "VALUES (%s, %s, %s, %s)"
            )
            update_sql = (
                "UPDATE products_amc SET stock = stock + %s WHERE id_product = %s"
            )
            self.cursor.execute(search_sql, (id_product,))
            result = self.cursor.fetchone()

            if result:
                return "Product already exists"

            self.cursor.execute(
                insert_sql, (id_product, movement_type, quantity, movement_date)
            )
            self.cursor.execute(update_sql, (quantity, id_product))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def update_in_movement(self, id_movement, quantity, movement_date):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            # Consulta para obtener la cantidad actual del movimiento
            current_entry_stock = (
                "SELECT quantity FROM product_movements_amc WHERE id_movement = %s"
            )
            self.cursor.execute(current_entry_stock, (id_movement,))
            entry_stock = self.cursor.fetchone()[0]

            # Consulta para obtener el stock actual del producto
            current_inventory_stock = "SELECT stock FROM products_amc WHERE id_product = (SELECT id_product FROM product_movements_amc WHERE id_movement = %s)"
            self.cursor.execute(current_inventory_stock, (id_movement,))
            inventory_stock = self.cursor.fetchone()[0]

            # Actualizar el movimiento del producto
            update_sql = "UPDATE product_movements_amc SET quantity = %s, movement_date = %s WHERE id_movement = %s"
            self.cursor.execute(update_sql, (quantity, movement_date, id_movement))

            # calculate the new stock
            new_stock = int(inventory_stock) - int(entry_stock) + int(quantity)
            # Actualizar el stock del producto
            update_inventory_stock = "UPDATE products_amc SET stock = %s WHERE id_product = (SELECT id_product FROM product_movements_amc WHERE id_movement = %s)"
            self.cursor.execute(update_inventory_stock, (new_stock, id_movement))

            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def delete_in_movement(self, id_movement):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            delete_sql = "DELETE FROM product_movements_amc WHERE id_movement = %s"
            update_sql = """
                UPDATE products_amc
                SET stock = stock - (SELECT quantity FROM product_movements_amc WHERE id_movement = %s)
                WHERE id_product = (SELECT id_product FROM product_movements_amc WHERE id_movement = %s)
                """
            self.cursor.execute(update_sql, (id_movement, id_movement))
            self.cursor.execute(delete_sql, (id_movement,))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_outs(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                """
                    SELECT product_movements_amc.*, products_amc.name as product_name
                    FROM product_movements_amc
                    JOIN products_amc ON product_movements_amc.id_product = products_amc.id_product
                    WHERE product_movements_amc.movement_type = 'salida';
                """
            )
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def create_out_movement(self, id_product, movement_type, quantity, movement_date):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"INSERT INTO product_movements_amc (id_product, movement_type, quantity, movement_date) VALUES ('{id_product}', '{movement_type}', '{quantity}', '{movement_date}')"
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

    def update_out_movement(self, id_movement, quantity, movement_date):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"UPDATE product_movements_amc SET quantity = '{quantity}', movement_date = '{movement_date}' WHERE id_movement = {id_movement}"
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

    def delete_out_movement(self, id_movement):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM product_movements_amc WHERE id_movement = {id_movement}"
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
