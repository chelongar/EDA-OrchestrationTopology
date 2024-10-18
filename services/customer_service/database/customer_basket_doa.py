from sqlalchemy.orm import Session
from .customer_model import customer_basket, customer_basket_item


class customer_basket_doa:
    def __init__(self, session: Session):
        self.current_session = session

    def create_basket(self, customer):
        _customer_basket = customer_basket(customer=customer)
        self.current_session.add(_customer_basket)
        self.current_session.commit()
        return _customer_basket

    def get_basket_by_customer(self, customer):
        return self.current_session.query(customer_basket).filter_by(customer_id=customer.customer_id).first().to_json()

    def get_basket_by_customer_json(self, customer):
        return self.current_session.query(customer_basket).filter_by(customer_id=customer.customer_id).first()

    def add_product_to_basket(self, customer_basket, author, title, isbn, price, publisher, quantity):
        try:
            customer_basket_attributes = {'author': author,
                                          'title': title,
                                          'isbn': isbn,
                                          'price': price,
                                          'quantity': quantity,
                                          'publisher': publisher,
                                          'customer_basket': customer_basket}
            customer_basket.customer_basket_item.append(customer_basket_item(**customer_basket_attributes))
            self.current_session.commit()

            return {'add_product_to_basket': 'Adding Item to Basket Done Successfully'}
        except Exception as err:
            msg = 'Adding Item to Basket Failed ' + str(err)
            return {'add_product_to_basket': msg}

    def decrement_item_from_basket(self, customer_basket_id, isbn):
        try:
            basket_item = self.current_session.query(customer_basket_item).filter_by(customer_basket_id=customer_basket_id,
                                                                                     isbn=isbn).first()
            if basket_item:
                self.current_session.delete(basket_item)
                self.current_session.commit()
                return {'decrement_item_from_basket': 'Decrementing Item to Basket Done Successfully'}
        except Exception as err:
            # Rollback in case of error to prevent partial commits
            self.current_session.rollback()
            msg = 'Decrementing Item to Basket Failed ' + str(err)
            return {'decrement_item_from_basket': msg}

    def remove_item_from_basket(self, customer_basket_id, isbn):
        try:
            items = self.current_session.query(customer_basket_item).filter_by(customer_basket_id=customer_basket_id,
                                                                               isbn=isbn).all()
            for _item in items:
                self.current_session.delete(_item)

            self.current_session.commit()

            return {'remove_item_from_basket': 'Removing items from basket done successfully'}

        except Exception as err:
            self.current_session.rollback()
            msg = 'Removing item from basket failed: ' + str(err)
            return {'remove_item_from_basket': msg}

    def get_basket_items(self, basket_id):
        return self.current_session.query(customer_basket_item).filter_by(basket_id=basket_id).all()

    def clear_basket(self, customer_basket_id):
        try:
            self.current_session.query(customer_basket_item).filter_by(customer_basket_id=customer_basket_id).delete()
            self.current_session.commit()

            return {'clear_basket': 'Clearing basket done successfully'}
        except Exception as err:
            self.current_session.rollback()
            msg = 'Clearing basket failed: ' + str(err)
            return {'clear_basket': msg}
