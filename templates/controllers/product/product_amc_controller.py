from templates.controllers.product.p_and_s_controller import update_stock_db, delete_product_db, update_product_db, \
    get_all_products_db, create_product_db, create_product_db_admin


class Product:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def create_product(self, sku, name, udm, stock, id_category, id_supplier, is_tool=0, is_internal=0):
        if id_supplier is not None:
            flag, error, result = create_product_db(sku, name, udm, stock, id_category, id_supplier, is_tool, is_internal)
        else:
            flag, error, result = create_product_db_admin(sku, name, udm, stock, id_category)
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
