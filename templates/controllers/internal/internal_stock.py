from templates.database.connection import connectionDB as db


class InternalStock:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def fetch_internal_stock(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = "SELECT * from internal_tools_amc"
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

    def create_product_internal(self, sku, name, contract_assigned, stock):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            search_sql = "SELECT * FROM internal_tools_amc WHERE sku = %s"
            inser_sql = "INSERT INTO internal_tools_amc (sku, name, contract_assigned, stock) VALUES (%s, %s, %s, %s)"
            self.cursor.execute(search_sql, (sku,))
            result = self.cursor.fetchone()
            if result:
                return "Product already exists"
            self.cursor.execute(inser_sql, (sku, name, contract_assigned, stock))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def update_product_internal(self, id_product, sku, name, contract_assigned, stock):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            update_sql = "UPDATE internal_tools_amc SET sku = %s, name = %s, contract_assigned = %s, stock = %s WHERE id_tool = %s"
            self.cursor.execute(
                update_sql, (sku, name, contract_assigned, stock, id_product)
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

    def delete_product_internal(self, id_product):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            delete_sql = "DELETE FROM internal_tools_amc WHERE id_tool = %s"
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

    def fetch_supply_stock(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = "SELECT * from supply_inventory_amc"
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

    def create_product_supply(self, sku, name, stock):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            search_sql = "SELECT * FROM supply_inventory_amc WHERE sku = %s"
            insert_sql = "INSERT INTO supply_inventory_amc (sku, name, stock) VALUES (%s, %s, %s)"
            self.cursor.execute(search_sql, (sku,))
            result = self.cursor.fetchone()
            if result:
                return "Product already exists"
            self.cursor.execute(insert_sql, (sku, name, stock))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def update_product_supply(self, id_product, sku, name, stock):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            update_sql = "UPDATE supply_inventory_amc SET sku = %s, name = %s, stock = %s WHERE id_supply = %s"
            self.cursor.execute(update_sql, (sku, name, stock, id_product))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def delete_product_supply(self, id_product):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            delete_sql = "DELETE FROM supply_inventory_amc WHERE id_supply = %s"
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
