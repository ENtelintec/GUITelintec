from templates.controllers.customer.customer_controller import Customer
from templates.controllers.order.details_controller import Details
from templates.controllers.order.order_amc_controller import Order
from templates.controllers.product.categories_controller import Category
from templates.controllers.product.movements_controller import Movement
from templates.controllers.product.product_amc_controller import Product
from templates.controllers.supplier.supplier_amc_controller import Supplier
from templates.controllers.internal.internal_stock import InternalStock


class DataHandler:
    def __init__(self):
        self._customer = Customer()
        self._order = Order()
        self._order_details = Details()
        self._product = Product()
        self._product_categories = Category()
        self._product_movements = Movement()
        self._supplier = Supplier()
        self._internal_stock = InternalStock()
    
    def get_all_products(self):
        return self._product.get_all_products()
    
    def get_ins(self):
        return self._product_movements.get_ins()
    
    def update_in_movement(self, id_movement, quantity, date):
        return self._product_movements.update_in_movement(id_movement, quantity, date, sm_id=None)
    
    def create_in_movement(self, id_product, id_movement_type, quantity, movement_date, sm_id=None):
        return self._product_movements.create_in_movement(id_product, id_movement_type, quantity, movement_date, sm_id)
    
    def delete_in_movement(self, movetement_id):
        return self._product_movements.delete_in_movement(movetement_id)

    def get_all_categories(self):
        return self._product_categories.get_all_categories()

    def create_category(self, name):
        return self._product_categories.create_category(name)

    def create_product(self, sku, name, udm, stock, id_category, id_supplier):
        return self._product.create_product(sku, name, udm, stock, id_category, id_supplier)

    def delete_product(self, product_id):
        return self._product.delete_product(product_id)

    def update_product(self, product_id, product_name, product_description, product_price, 
                       product_stock, product_category, product_supplier):
        return self._product.update_product(product_id, product_name, product_description, product_price,
                                            product_stock, product_category, product_supplier)

    def update_stock(self, id_product, stock):
        return self._product.update_stock(id_product, stock)

    def get_outs(self):
        return self._product_movements.get_outs()

    def create_out_movement(self, product_id, movement_type, quantity, date, sm_id):
        return self._product_movements.create_out_movement(product_id, movement_type, quantity, date, sm_id)

    def update_out_movement(self, movetement_id, quantity, new_date, sm_id):
        return self._product_movements.update_out_movement(movetement_id, quantity, new_date, sm_id)

    def delete_out_movement(self, movetement_id):
        return self._product_movements.delete_out_movement(movetement_id)

    def get_all_customers(self):
        return self._customer.get_all_customers()

    def create_customer(self, name, email, phone, rfc, address):
        return self._customer.create_customer(name, email, phone, rfc, address)

    def update_customer(self, id_customer, name, email, phone, rfc, address):
        return self._customer.update_customer(id_customer, name, email, phone, rfc, address)

    def delete_customer(self, id_customer):
        return self._customer.delete_customer(id_customer)
