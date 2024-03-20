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
            sku = str(sku)
            name = str(name)
            udm = str(udm)
            stock = int(stock)
            minStock = int(minStock)
            maxStock = int(maxStock)
            reorderPoint = int(reorderPoint)
            id_category = int(id_category)
            search_sql = "SELECT * FROM products_amc WHERE name = %s"
            self.cursor.execute(search_sql, (name,))
            result = self.cursor.fetchone()
            if result:
                return "Product already exists"

            insert_sql = "INSERT INTO products_amc (sku, name, udm, stock, minStock, maxStock, reorderPoint, id_category) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            self.cursor.execute(
                insert_sql,
                (sku, name, udm, stock, minStock, maxStock, reorderPoint, id_category),
            )
            self.connection.commit()
            insert_supplier_product_sql = "INSERT INTO supplier_product_amc (id_supplier, id_product) VALUES (%s, %s)"
            self.cursor.execute(
                insert_supplier_product_sql, (id_supplier, self.cursor.lastrowid)
            )
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
            update_sql = "UPDATE products_amc SET sku = %s, name = %s, udm = %s, stock = %s, minStock = %s, maxStock = %s, reorderPoint = %s, id_category = %s WHERE id_product = %s"
            self.cursor.execute(
                update_sql,
                (
                    sku,
                    name,
                    udm,
                    stock,
                    minStock,
                    maxStock,
                    reorderPoint,
                    id_category,
                    id_product,
                ),
            )
            self.connection.commit()
            update_relation_sql = (
                "UPDATE supplier_product_amc SET id_supplier = %s WHERE id_product = %s"
            )
            self.cursor.execute(update_relation_sql, (id_supplier, id_product))
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
            delete_sql = "DELETE FROM products_amc WHERE id_product = %s"
            self.cursor.execute(delete_sql, (id_product,))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None
