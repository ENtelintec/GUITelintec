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
            sql = (
                f"INSERT INTO product_movements_amc (id_product, movement_type, quantity, movement_date) "
                f"VALUES ('{id_product}', '{movement_type}', '{quantity}', '{movement_date}')"
            )
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

    def update_in_movement(self, id_movement, quantity, movement_date):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = (
                f"UPDATE product_movements_amc SET quantity = '{quantity}', movement_date = '{movement_date}' "
                f"WHERE id_movement = {id_movement}"
            )
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

    def delete_in_movement(self, id_movement):
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
