from database.connection import connectionDB as db


class Product:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_all_products(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute("SELECT * FROM supplier_products")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_single_product(self, id_product):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                f"SELECT * FROM supplier_products WHERE id = {id_product}"
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

    def update_product(self, id_product, name, id_category, id_supplier, price, stock):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"UPDATE supplier_products SET name = '{name}', id_category = '{id_category}', id_supplier = '{id_supplier}', price = '{price}', stock = '{stock}' WHERE id = {id_product}"
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

    def delete_product(self, id_product):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM supplier_products WHERE id = {id_product}"
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
