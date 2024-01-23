from templates.controllers.customer.address_controller import Address
from templates.controllers.customer.customer_controller import Customer
from templates.controllers.order.details_controller import Details
from templates.controllers.order.order_controller import Order
from templates.controllers.product.categories_controller import Category
from templates.controllers.product.movements_controller import Movement
from templates.controllers.product.product_controller import Product
from templates.controllers.supplier.products_controller import Product as SupplierProduct
from templates.controllers.supplier.suppliers_controller import Supplier


class DataHandler:
    def __init__(self):
        self._customer = Customer()
        self._customer_address = Address()
        self._order = Order()
        self._order_details = Details()
        self._product = Product()
        self._product_categories = Category()
        self._product_movements = Movement()
        self._supplier = Supplier()
        self._supplier_product = SupplierProduct()
