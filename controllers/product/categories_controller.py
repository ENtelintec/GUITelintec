from database.connection import connectionDB as db


class Category:
    def __init__(self):
        self.connection = db()
        self.cursor = self.connection.cursor()

    def get_all_categories(self):
        try:
            self.cursor.execute("SELECT * FROM product_categories")
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def get_single_category(self, id_category):
        try:
            self.cursor.execute(
                f"SELECT * FROM product_categories WHERE id = {id_category}")
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def update_category(self, id_category, name):
        try:
            sql = (f"UPDATE product_categories SET name = '{name}' "
                   f"WHERE id = {id_category}")
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()

    def delete_category(self, id_category):
        try:
            sql = f"DELETE FROM product_categories WHERE id = {id_category}"
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except Exception as e:
            return f'Error: {e}'
        finally:
            self.cursor.close()
            self.connection.close()
