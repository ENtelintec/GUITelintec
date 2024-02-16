from templates.database.connection import connectionDB as db


class InternalStock:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def fetch_internal_stock(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"SELECT * from internal_tools_amc"
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
            sql = f"INSERT INTO internal_tools_amc (sku, name, contract_assigned, stock) VALUES ('{sku}', '{name}', '{contract_assigned}', {stock})"
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

    def update_product_internal(self, id_product, sku, name, contract_assigned, stock):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"UPDATE internal_tools_amc SET sku = '{sku}', name = '{name}', contract_assigned = '{contract_assigned}', stock = {stock} WHERE id_tool = {id_product}"
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

    def delete_product_internal(self, id_product):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM internal_tools_amc WHERE id_tool = {id_product}"
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

    def fetch_supply_stock(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"SELECT * from supply_inventory_amc"
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
            sql = f"INSERT INTO supply_inventory_amc (sku, name, stock) VALUES ('{sku}', '{name}', {stock})"
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

    def update_product_supply(self, id_product, sku, name, stock):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"UPDATE supply_inventory_amc SET sku = '{sku}', name = '{name}', stock = {stock} WHERE id_supply = {id_product}"
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

    def delete_product_supply(self, id_product):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM supply_inventory_amc WHERE id_supply = {id_product}"
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
