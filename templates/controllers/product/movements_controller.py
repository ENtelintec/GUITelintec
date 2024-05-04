from templates.controllers.product.p_and_s_controller import get_ins_db, create_in_movement_db, update_movement_db, \
    delete_movement_db, get_outs_db, create_out_movement_db


class Movement:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_ins(self):
        flag, e, result = get_ins_db()
        if flag:
            return result
        else:
            print(e)
            return []

    def create_in_movement(self, id_product, movement_type, quantity, movement_date, sm_id):
        flag, e, result = create_in_movement_db(id_product, movement_type, quantity, movement_date, sm_id)
        return flag

    def update_in_movement(self, id_movement, quantity, movement_date, sm_id):
        flag, e, result = update_movement_db(id_movement, quantity, movement_date, sm_id)
        return flag

    def delete_in_movement(self, id_movement):
        flag, e, result = delete_movement_db(id_movement)
        return flag

    def get_outs(self):
        flag, e, result = get_outs_db()
        if flag:
            return result
        else:
            print(e)
            return []

    def create_out_movement(self, id_product, movement_type, quantity, movement_date, sm_id):
        flag, e, result = create_out_movement_db(id_product, movement_type, quantity, movement_date, sm_id)
        return flag

    def update_out_movement(self, id_movement, quantity, movement_date, sm_id):
        flag, e, result = update_movement_db(id_movement, quantity, movement_date, sm_id)
        return flag

    def delete_out_movement(self, id_movement):
        flag, e, result = delete_movement_db(id_movement)
        return flag
