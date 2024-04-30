from templates.controllers.product.Functions_SQL import update_stock_db, delete_product_db, update_product_db, \
    get_all_products_db, create_product_db


class Product:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def create_product(self, sku, name, udm, stock, id_category, id_supplier):
        flag, error, result = create_product_db(sku, name, udm, stock, id_category, id_supplier)
        return flag

    def get_all_products(self):
        flag, error, result = get_all_products_db()
        return result if flag else []

    def update_product(self, id_product, sku, name, udm, stock, id_category, id_supplier):
        flag, error, result = update_product_db(id_product, sku, name, udm, stock, id_category, id_supplier)
        return flag

    def delete_product(self, id_product):
        flag, error, result = delete_product_db(id_product)
        return flag

    def update_stock(self, id_product, stock):
        flag, error, result = update_stock_db(id_product, stock)
        return flag
