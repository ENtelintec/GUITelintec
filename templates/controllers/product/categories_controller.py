from templates.database.connection import connectionDB as db


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

    def create_category(self, name):
        try:
            self.connection = db()
            self.cursor = self.connection.cursor()
            name = str(name)
            insert_sql = "INSERT INTO product_categories_amc (name) VALUES (%s)"
            find_sql = "SELECT * FROM product_categories_amc WHERE name = %s"
            self.cursor.execute(find_sql, (name,))
            result = self.cursor.fetchone()

            if result:
                return "Category already exists"

            self.cursor.execute(insert_sql, (name,))
            self.connection.commit()
            return True
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
            update_sql = "UPDATE product_categories_amc SET name = %s WHERE id = %s"
            self.cursor.execute(update_sql, (name, id_category))
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
            delete_sql = "DELETE FROM product_categories_amc WHERE id = %s"
            self.cursor.execute(delete_sql, (id_category,))
            self.connection.commit()
            return True
        except Exception as e:
            return f"Error: {e}"
        finally:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                self.cursor = None
