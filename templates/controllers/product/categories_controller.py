from templates.controllers.product.p_and_s_controller import get_all_categories_db, create_category_db, update_category_db, \
    delete_category_db


class Category:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_all_categories(self):
        flag, error, result = get_all_categories_db()
        return result if flag else []

    def create_category(self, name):
        flag, error, result = create_category_db(name)
        return flag

    def update_category(self, id_category, name):
        flag, error, result = update_category_db(id_category, name)
        return flag

    def delete_category(self, id_category):
        flag, error, result = delete_category_db(id_category)
        return flag
