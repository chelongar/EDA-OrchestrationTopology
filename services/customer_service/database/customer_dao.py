import json
from sqlalchemy.orm import Session

from .customer_model import customer, customer_address, customer_basket, customer_basket_item


class customer_dao:
    def __init__(self, session: Session):
        self.session = session

    def load_customers_from_json_file(self, products_file_path):
        try:
            with open(products_file_path, 'r') as file:
                customers_data = json.load(file)

                for customer_data in customers_data:
                    customer_attributes = {
                        'customer_first_name': customer_data['customer_first_name'],
                        'customer_last_name': customer_data['customer_last_name'],
                        'customer_username': customer_data['customer_username'],
                        'customer_password': customer_data['customer_password'],
                        'customer_email': customer_data['customer_email'],
                        'customer_phone_number': customer_data['customer_phone_number']
                    }
                    _customer = customer(**customer_attributes)

                    addresses_data = customer_data['customer_address']
                    addresses = []
                    for address_data in addresses_data:
                        _address = customer_address(**address_data)
                        addresses.append(_address)

                    # Associate addresses with the customer
                    _customer.customer_address = addresses

                    # Create Basket object
                    _customer_basket = customer_basket(customer=_customer)

                    _customer_basket_items = customer_data['customer_basket']
                    for _item in _customer_basket_items:
                        customer_basket_attributes = {'author': _item['Author'],
                                                      'title': _item['Title'],
                                                      'isbn': _item['ISBN'],
                                                      'price': _item['Price'],
                                                      'quantity': _item['Count'],
                                                      'publisher': _item['Publisher'],
                                                      'customer_basket': _customer_basket}
                        _customer_basket.customer_basket_item.append(customer_basket_item(**customer_basket_attributes))

                    self.session.add(_customer)
                    self.session.commit()
                return {'load_customers_information': 'Done Successfully'}
        except FileNotFoundError as err:
            print(f"File '{products_file_path}' not found.")

            return {'load_customers_information': err}
        except json.JSONDecodeError as err:
            print(f"Error in decoding JSON file: {err}")

            return {'load_customers_information': err}

    def get_all_customers(self):
        return self.session.query(customer).all()

    def get_all_customers_json(self):
        all_customers = self.session.query(customer).all()
        return [_customer.to_json() for _customer in all_customers]

    def get_customer_by_last_name(self, customer_last_name):
        return self.session.query(customer).filter(customer.customer_last_name == customer_last_name).first()

    def get_customer_by_last_name_json(self, customer_last_name):
        _customer = self.session.query(customer).filter(customer.customer_last_name == customer_last_name).first()
        return _customer.to_json()

    def get_customer_by_username_json(self, customer_username):
        _customer = self.session.query(customer).filter(customer.customer_username == customer_username).first()
        return _customer.to_json()

    def get_customer_by_email(self, email):
        return self.session.query(customer).filter(customer.customer_email == email).first()

    def get_customer_by_email_json(self, email):
        _customer = self.session.query(customer).filter(customer.customer_email == email).first()
        return _customer.to_json()

    def add_customer(self, _customer):
        self.session.add(_customer)
        self.session.commit()
        return _customer

    # noinspection PyBroadException
    def add_customer_by_parameters(self, customer_first_name: str, customer_last_name: str,
                                   customer_email: str, customer_username: str, customer_password: str,
                                   customer_phone_number: str, customer_addresses: dict):
        try:
            customer_attributes = {
                'customer_first_name': customer_first_name,
                'customer_last_name': customer_last_name,
                'customer_username': customer_username,
                'customer_password': customer_password,
                'customer_email': customer_email,
                'customer_phone_number': customer_phone_number
            }
            _customer = customer(**customer_attributes)

            addresses = []
            _address = customer_address(**customer_addresses)
            addresses.append(_address)

            # Associate addresses with the customer
            _customer.customer_address = addresses

            self.session.add(_customer)
            self.session.commit()

            return {'customer_sign_up': 'Signed Up Successfully'}
        except Exception as error:
            msg = 'Signed Up Failed' + error
            return {'customer_sign_up': msg}

    def delete_customer_by_email(self, email):
        _customer = self.get_customer_by_email(email)
        if _customer:
            self.session.delete(_customer)
            self.session.commit()
            return True

        return False

    def close_session(self):
        self.session.close()
