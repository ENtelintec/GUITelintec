from database.connection import connectionDB as db


class Product:
    def __init__(self):
        self.connection = db()
        self.cursor = self.connection.cursor()

    def get_all_products(self):
        try:
            self.cursor.execute("SELECT * FROM supplier_products")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def get_single_product(self, id_product):
        try:
            self.cursor.execute(
                f"SELECT * FROM supplier_products WHERE id = {id_product}")
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def update_product(self, id_product, name, id_category, id_supplier, price, stock):
        try:
            sql = f"UPDATE supplier_products SET name = '{name}', id_category = '{id_category}', id_supplier = '{id_supplier}', price = '{price}', stock = '{stock}' WHERE id = {id_product}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def delete_product(self, id_product):
        try:
            sql = f"DELETE FROM supplier_products WHERE id = {id_product}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()
