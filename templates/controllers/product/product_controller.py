from templates.database.connection import connectionDB as db


class Product:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def create_product(
        self,
        sku,
        name,
        udm,
        stock,
        minStock,
        maxStock,
        reorderPoint,
        id_category,
        id_supplier,
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"INSERT INTO products_amc (sku, name, udm, stock, minStock, maxStock, reorderPoint, id_category) VALUES ('{sku}', '{name}', '{udm}', {stock}, {minStock}, {maxStock}, {reorderPoint}, {id_category})"
            self.cursor.execute(sql)
            self.connection.commit()

            sql2 = f"INSERT INTO supplier_product_amc (id_supplier, id_product) VALUES ({id_supplier}, {self.cursor.lastrowid})"
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

    def get_all_products(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"SELECT * from get_all_products"
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

    def update_product(
        self,
        id_product,
        sku,
        name,
        udm,
        stock,
        minStock,
        maxStock,
        reorderPoint,
        id_category,
        id_supplier,
    ):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"UPDATE products_amc SET sku = '{sku}', name = '{name}', udm = '{udm}', stock = {stock}, minStock = {minStock}, maxStock = {maxStock}, reorderPoint = {reorderPoint}, id_category = {id_category} WHERE id_product = {id_product}"
            self.cursor.execute(sql)
            self.connection.commit()

            sql2 = f"UPDATE supplier_product_amc SET id_supplier = {id_supplier} WHERE id_product = {id_product}"
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

    def delete_product(self, id_product):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql2 = f"DELETE FROM products_amc WHERE id_product = {id_product}"
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
