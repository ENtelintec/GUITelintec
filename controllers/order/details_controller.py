from database.connection import connectionDB as db


class Details:
    def __init__(self):
        self.connection = db()
        self.cursor = self.connection.cursor()

    def get_all_details(self):
        try:
            self.cursor.execute("SELECT * FROM order_details_amc")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def get_single_detail(self, id_detail):
        try:
            self.cursor.execute(
                f"SELECT * FROM order_details WHERE id = {id_detail}")
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def update_detail(self, id_detail, id_order, id_product, quantity, price):
        try:
            sql = (f"UPDATE order_details SET id_order = '{id_order}', id_product = '{id_product}', quantity = '{quantity}', price = '{price}' "
                   f"WHERE id = {id_detail}")
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def delete_detail(self, id_detail):
        try:
            sql = f"DELETE FROM order_details WHERE id = {id_detail}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()
