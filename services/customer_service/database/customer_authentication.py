from .customer_model import customer


class customer_authentication:
    def __init__(self, session):
        self.current_session = session
        self.current_customer = None

    def customer_login(self, customer_username, customer_password):
        _customer = self.current_session.query(customer).filter_by(customer_username=customer_username).first()
        if _customer and _customer.customer_password == customer_password:
            self.current_customer = _customer
            return {'customer_sign_in': 'Login Was Successful'}
        return {'customer_sign_in': 'Failed'}

    def customer_logout(self):
        self.current_customer = None
        self.current_session.remove()

    def get_current_customer(self):
        return self.current_customer
