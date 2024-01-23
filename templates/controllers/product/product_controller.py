from templates.database.connection import connectionDB as db


class Product:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def create_product(
        self,
        name,
        description,
        price,
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
            sql = (
                f"INSERT INTO products_amc (name, description, price, stock, id_category) "
                f"VALUES ('{name}', '{description}', {price}, {stock}, {minStock}, {maxStock}, {reorderPoint}, {id_category})"
            )
            self.cursor.execute(sql)
            self.connection.commit()

            sql2 = (
                f"INSERT INTO supplier_product_amc (id_supplier, id_product) "
                f"VALUES ({id_supplier}, {self.cursor.lastrowid})"
            )
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
            sql = """
            SELECT products_amc.id_product,
                products_amc.name AS product_name,
                products_amc.description,
                products_amc.price,
                products_amc.stock,
                products_amc.minStock,
                products_amc.maxStock,
                products_amc.reorderPoint,
                product_categories_amc.name AS category_name,
                suppliers_amc.name AS supplier_name
            FROM products_amc
            LEFT JOIN product_categories_amc ON products_amc.id_category = product_categories_amc.id_category
            LEFT JOIN supplier_product_amc ON products_amc.id_product = supplier_product_amc.id_product
            LEFT JOIN suppliers_amc ON supplier_product_amc.id_supplier = suppliers_amc.id_supplier"""
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
        name,
        description,
        price,
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
            sql = (
                f"UPDATE products_amc SET name = '{name}', description = '{description}', price = {price}, stock = {stock}, minStock= {minStock}, maxStock = {maxStock}, reorderPoint = {reorderPoint}, id_category = {id_category} "
                f"WHERE id_product = {id_product}"
            )
            self.cursor.execute(sql)
            self.connection.commit()
            sql2 = (
                f"UPDATE supplier_product_amc SET id_supplier = {id_supplier} "
                f"WHERE id_product = {id_product}"
            )
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
