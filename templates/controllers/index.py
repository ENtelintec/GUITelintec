from templates.controllers.customer.customer_controller import Customer
from templates.controllers.order.details_controller import Details
from templates.controllers.order.order_controller import Order
from templates.controllers.product.categories_controller import Category
from templates.controllers.product.movements_controller import Movement
from templates.controllers.product.product_controller import Product
from templates.controllers.supplier.suppliers_controller import Supplier
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
