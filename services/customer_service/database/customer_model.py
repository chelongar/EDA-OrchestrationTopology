#!/usr/bin/python

from sqlalchemy import Column, Integer, Text, String, ForeignKey
from sqlalchemy.orm import relationship

from .database_models import Base


class customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True)
    customer_first_name = Column(Text, nullable=False)
    customer_last_name = Column(Text, nullable=False)
    customer_username = Column(Text, nullable=False, unique=True)
    customer_password = Column(Text, nullable=False)
    customer_email = Column(Text, nullable=False, unique=True)
    customer_phone_number = Column(Text, nullable=True)
    customer_address = relationship("customer_address", back_populates="customer", cascade="all, delete-orphan", lazy='joined')
    customer_basket = relationship('customer_basket', back_populates='customer', cascade='all, delete-orphan', lazy='joined')

    def __repr__(self):
        return f"customer(first_name={self.customer_first_name}, " \
               f"customer_id={self.customer_id} " \
               f"last_name={self.customer_last_name}, " \
               f"username={self.customer_username}, " \
               f"E-Mail={self.customer_email}, " \
               f"phone_number={self.customer_phone_number}, " \
               f"customer_address={[_customer_address for _customer_address in self.customer_address if _customer_address.customer_id == self.customer_id]})"

    def to_json(self):
        return {'customer_id': self.customer_id,
                'last_name': self.customer_last_name,
                'first_name': self.customer_first_name,
                'username': self.customer_username,
                'email': self.customer_email,
                'addresses': [_customer_address.to_json() for _customer_address in self.customer_address if _customer_address.customer_id == self.customer_id],
                'customer_basket': [_customer_basket.to_json() for _customer_basket in self.customer_basket if _customer_basket.customer_basket_id == self.customer_id]}


class customer_address(Base):
    __tablename__ = 'customer_addresses'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    street = Column(String)
    city = Column(String)
    country = Column(String)
    zip_code = Column(String)
    customer = relationship("customer", back_populates="customer_address")

    def __repr__(self):
        return f"customer_address(street={self.street}, " \
               f"city={self.city}, " \
               f"country={self.country}, " \
               f"zip_code={self.zip_code}, " \
               f"customer_id={self.customer_id})"

    def to_json(self):
        return {"street": self.street,
                "county": self.country,
                "city": self.city,
                "zip_code": self.zip_code}


class customer_basket(Base):
    __tablename__ = 'customer_baskets'
    customer_basket_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    customer = relationship('customer', back_populates='customer_basket')
    customer_basket_item = relationship('customer_basket_item', back_populates='customer_basket', cascade='all, delete-orphan')

    def __repr__(self):
        return (f"customer_basket(customer_basket_id={self.customer_basket_id}, "
                f"basket_items={[basket_item.__repr__() for basket_item in self.customer_basket_item]})")

    def to_json(self):
        return {"customer_basket_id": self.customer_basket_id,
                "basket_items": [basket_item.to_json() for basket_item in self.customer_basket_item]}

class customer_basket_item(Base):
    __tablename__ = 'customer_basket_items'
    id = Column(Integer, primary_key=True)
    customer_basket_id = Column(Integer, ForeignKey('customer_baskets.customer_basket_id'), nullable=False)
    author = Column(String, nullable=False)
    title = Column(String, nullable=False)
    isbn = Column(String, nullable=False)
    price = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    publisher = Column(String, nullable=False)
    customer_basket = relationship('customer_basket', back_populates='customer_basket_item')

    def __repr__(self):
        return f"customer_basket_item(Author={self.author}, " \
               f"Title={self.title}, " \
               f"ISBN={self.isbn}, " \
               f"Price={self.price}, " \
               f"Count={self.quantity}, " \
               f"Publisher={self.publisher})"

    def to_json(self):
        return {"Author": self.author,
                "Title": self.title,
                "ISBN": self.isbn,
                "Price": self.price,
                "Count": self.quantity,
                "Publisher": self.publisher}
