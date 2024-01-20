from database.connection import connectionDB as db


class Category:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_all_categories(self):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute("SELECT * FROM product_categories_amc")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None

    def get_single_category(self, id_category):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                f"SELECT * FROM product_categories_amc WHERE id = {id_category}"
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

    def update_category(self, id_category, name):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = (
                f"UPDATE product_categories_amc SET name = '{name}' "
                f"WHERE id = {id_category}"
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

    def delete_category(self, id_category):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            sql = f"DELETE FROM product_categories_amc WHERE id = {id_category}"
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
