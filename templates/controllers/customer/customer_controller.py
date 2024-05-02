from templates.controllers.customer.customers_controller import delete_customer_db, update_customer_db, create_customer_db, \
    get_all_customers_db


class Customer:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_all_customers(self):
        flag, error, result = get_all_customers_db()
        return result if flag else []

    def create_customer(self, name, email, phone, rfc, address):
        flag, error, result = create_customer_db(name, email, phone, rfc, address)
        return flag

    def update_customer(self, id_customer, name, email, phone, rfc, address):
        flag, error, result = update_customer_db(id_customer, name, email, phone, rfc, address)
        return flag

    def delete_customer(self, id_customer):
        flag, error, result = delete_customer_db(id_customer)
        return flag
