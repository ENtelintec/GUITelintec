from database.connection import connectionDB as db


class Movement:
    def __init__(self):
        self.connection = db()
        self.cursor = self.connection.cursor()

    def get_ins(self):
        try:
            self.cursor.execute(
                """
                    SELECT product_movements.*, products.name as product_name
                    FROM product_movements
                    JOIN products ON product_movements.id_product = products.id_product
                    WHERE product_movements.movement_type = 'entrada';
                """)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'

    def create_in_movement(self, id_product, movement_type, quantity, movement_date):
        try:
            sql = (f"INSERT INTO product_movements (id_product, movement_type, quantity, movement_date) "
                   f"VALUES ('{id_product}', '{movement_type}', '{quantity}', '{movement_date}')")
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def update_in_movement(self, id_movement, quantity, movement_date):
        try:
            sql = (f"UPDATE product_movements SET quantity = '{quantity}', movement_date = '{movement_date}' "
                   f"WHERE id_movement = {id_movement}")
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def delete_in_movement(self, id_movement):
        try:
            sql = f"DELETE FROM product_movements WHERE id_movement = {id_movement}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def get_outs(self):
        try:
            self.cursor.execute(
                """
                    SELECT product_movements.*, products.name as product_name
                    FROM product_movements
                    JOIN products ON product_movements.id_product = products.id_product
                    WHERE product_movements.movement_type = 'salida';
                """)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'

    def create_out_movement(self, id_product, movement_type, quantity, movement_date):
        try:
            sql = f"INSERT INTO product_movements (id_product, movement_type, quantity, movement_date) VALUES ('{id_product}', '{movement_type}', '{quantity}', '{movement_date}')"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def update_out_movement(self, id_movement, quantity, movement_date):
        try:
            sql = f"UPDATE product_movements SET quantity = '{quantity}', movement_date = '{movement_date}' WHERE id_movement = {id_movement}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def delete_out_movement(self, id_movement):
        try:
            sql = f"DELETE FROM product_movements WHERE id_movement = {id_movement}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def close_connection(self):
        self.connection.close()
        self.cursor.close()
