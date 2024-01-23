from templates.database.connection import connectionDB as db


class Details:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_all_details(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute("SELECT * FROM order_details_amc")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_single_detail(self, id_detail):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute(f"SELECT * FROM order_details WHERE id = {id_detail}")
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def update_detail(self, id_detail, id_order, id_product, quantity, price):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = (
                f"UPDATE order_details SET id_order = '{id_order}', id_product = '{id_product}', quantity = '{quantity}', price = '{price}' "
                f"WHERE id = {id_detail}"
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

    def delete_detail(self, id_detail):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM order_details WHERE id = {id_detail}"
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
