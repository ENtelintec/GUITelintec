from templates.controllers.customer.customers_controller import delete_customer_db, update_customer_db, \
    create_customer_db, get_all_customers_db
from templates.controllers.product.p_and_s_controller import get_all_suppliers, create_product_db, \
    create_product_db_admin, update_product_db, delete_product_db, get_all_products_db, update_stock_db, \
    get_all_categories_db, create_category_db, update_category_db, delete_category_db, create_in_movement_db, \
    update_movement_db, delete_movement_db, get_outs_db, create_out_movement_db, get_ins_db
from templates.controllers.supplier.suppliers_controller import create_supplier_amc, update_supplier_amc, \
    delete_supplier_amc


class DataHandler:
    def __init__(self):
        self._customer = {
            "createCustomer": create_customer_db,
            "updateCustomer": update_customer_db,
            "deleteCustomer": delete_customer_db,
            "getAllCustomers": get_all_customers_db
        }
        self._product = {
            "createProduct": create_product_db,
            "createProductAdmin": create_product_db_admin,
            "updateProduct": update_product_db,
            "deleteProduct": delete_product_db,
            "getAllProducts": get_all_products_db,
            "updateStock": update_stock_db,
        }
        self._product_categories = {
            "getAllCategories": get_all_categories_db,
            "createCategory": create_category_db,
            "updateCategory": update_category_db,
            "deleteCategory": delete_category_db
        }
        self._product_movements = {
            "createInMovement": create_in_movement_db,
            "createOutMovement": create_out_movement_db,
            "updateMovement": update_movement_db,
            "deleteMovement": delete_movement_db,
            "get_ins": get_ins_db,
            "get_outs": get_outs_db,
        }
        self._supplier = {
            "getAllSuppliers": get_all_suppliers,
            "createSupplier": create_supplier_amc,
            "updateSupplier": update_supplier_amc,
            "deleteSupplier": delete_supplier_amc,

        }

    def get_all_products(self):
        function = self._product["getAllProducts"]
        flag, error, result = function()
        return result if flag else []

    def get_ins(self):
        flag, e, result = self._product_movements["get_ins"]()
        return result if flag else []

    def create_in_movement(self, id_product, movement_type, quantity, movement_date, sm_id):
        flag, e, result = self._product_movements["createInMovement"](id_product, movement_type, quantity,
                                                                      movement_date, sm_id)
        return flag

    def update_in_movement(self, id_movement, quantity, movement_date, sm_id):
        flag, e, result = self._product_movements["updateMovement"](id_movement, quantity, movement_date, sm_id)
        return flag

    def delete_in_movement(self, id_movement):
        flag, e, result = self._product_movements["deleteMovement"](id_movement)
        return flag

    def get_outs(self):
        flag, e, result = self._product_movements["get_outs"]()
        return result if flag else []

    def create_out_movement(self, id_product, movement_type, quantity, movement_date, sm_id):
        flag, e, result = self._product_movements["createOutMovement"](id_product, movement_type, quantity,
                                                                       movement_date, sm_id)
        return flag

    def update_out_movement(self, id_movement, quantity, movement_date, sm_id):
        flag, e, result = self._product_movements["updateMovement"](id_movement, quantity, movement_date, sm_id)
        return flag

    def delete_out_movement(self, id_movement):
        flag, e, result = self._product_movements["deleteMovement"](id_movement)
        return flag

    def get_all_categories(self):
        flag, error, result = self._product_categories["getAllCategories"]()
        return result if flag else []

    def create_category(self, name):
        flag, error, result = self._product_categories["createCategory"](name)
        return flag

    def update_category(self, id_category, name):
        flag, error, result = self._product_categories["updateCategory"](id_category, name)
        return flag

    def delete_category(self, id_category):
        flag, error, result = self._product_categories["deleteCategory"](id_category)
        return flag

    def create_product(self, sku, name, udm, stock, id_category, id_supplier, is_tool=0, is_internal=0):
        if id_supplier is not None:
            function = self._product["createProduct"]
            flag, error, result = function(sku, name, udm, stock, id_category, id_supplier, is_tool, is_internal)
            return result if flag else []
        else:
            function = self._product["createProductAdmin"]
            flag, error, result = function(sku, name, udm, stock, id_category)
            return result if flag else []

    def delete_product(self, product_id):
        function = self._product["deleteProduct"]
        flag, error, result = function(product_id)
        return flag

    def update_product(self, product_id, product_name, product_description, product_price,
                       product_stock, product_category, product_supplier, is_tool=0, is_internal=0):
        function = self._product["updateProduct"]
        flag, error, result = function(product_id, product_name, product_description, product_price,
                                       product_stock, product_category, product_supplier, is_tool, is_internal)
        return flag

    def update_stock(self, id_product, stock):
        function = self._product["updateStock"]
        flag, error, result = function(id_product, stock)
        return flag

    def get_all_customers(self):
        function = self._customer["getAllCustomers"]
        flag, error, result = function()
        return result if flag else []

    def create_customer(self, name, email, phone, rfc, address):
        function = self._customer["createCustomer"]
        flag, error, result = function(name, email, phone, rfc, address)
        return flag

    def update_customer(self, id_customer, name, email, phone, rfc, address):
        function = self._customer["updateCustomer"]
        flag, error, result = function(id_customer, name, email, phone, rfc, address)
        return flag

    def delete_customer(self, id_customer):
        function = self._customer["deleteCustomer"]
        flag, error, result = function(id_customer)
        return flag

    def get_all_suppliers(self):
        function = self._supplier["getAllSuppliers"]
        flag, error, result = function()
        return result if flag else []

    def create_supplier(self, name_provider, seller_provider, email_provider, phone_provider, address_provider,
                        web_provider, type_provider):
        function = self._supplier["createSupplier"]
        flag, error, result = function(name_provider, seller_provider, email_provider, phone_provider, address_provider,
                                       web_provider, type_provider)
        return flag

    def update_supplier(self, id_provider, name_provider, seller_provider, email_provider, phone_provider,
                        address_provider, web_provider, type_provider):
        function = self._supplier["updateSupplier"]
        flag, error, result = function(id_provider, name_provider, seller_provider, email_provider, phone_provider,
                                       address_provider, web_provider, type_provider)
        return flag

    def delete_supplier(self, id_supplier):
        function = self._supplier["deleteSupplier"]
        flag, error, result = function(id_supplier)
        return flag
