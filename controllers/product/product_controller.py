from database.connection import connectionDB as db


class Product:
    def __init__(self):
        self.connection = db()
        self.cursor = self.connection.cursor()

    def create_product(self, name, description, price, stock, id_category, id_supplier):
        try:
            sql = (f"INSERT INTO products (name, description, price, stock, id_category) "
                   f"VALUES ('{name}', '{description}', {price}, {stock}, {id_category})")
            self.cursor.execute(sql)
            self.connection.commit()

            sql2 = (f"INSERT INTO supplier_product (id_supplier, id_product) "
                    f"VALUES ({id_supplier}, {self.cursor.lastrowid})")
            self.cursor.execute(sql2)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def get_all_products(self):
        try:
            sql = """
            SELECT products.id_product, products.name AS product_name, products.description,
                products.price, products.stock, product_categories.name AS category_name,
                suppliers.name AS supplier_name
            FROM products
            LEFT JOIN product_categories ON products.id_category = product_categories.id_category
            LEFT JOIN supplier_product ON products.id_product = supplier_product.id_product
            LEFT JOIN suppliers ON supplier_product.id_supplier = suppliers.id_supplier"""
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'

    def get_single_product(self, id_product):
        try:
            self.cursor.execute(
                f"SELECT * FROM products WHERE id = {id_product}")
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            return f'Error: {e}'

    def update_product(self, id_product, name, description, price, stock, id_category, id_supplier):
        try:
            sql = (f"UPDATE products SET name = '{name}', description = '{description}', price = {price}, stock = {stock}, id_category = {id_category} "
                   f"WHERE id_product = {id_product}")
            self.cursor.execute(sql)
            self.connection.commit()
            sql2 = (f"UPDATE supplier_product SET id_supplier = {id_supplier} "
                    f"WHERE id_product = {id_product}")
            self.cursor.execute(sql2)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def delete_product(self, id_product):
        try:
            sql2 = f"DELETE FROM products WHERE id_product = {id_product}"
            self.cursor.execute(sql2)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'

    def close_connection(self):
        self.connection.close()
        self.cursor.close()
