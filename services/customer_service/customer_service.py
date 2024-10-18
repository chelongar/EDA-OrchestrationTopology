#!/usr/bin/python
import ast
import configparser
import json
import os

import pika
from RPC import rpc_server
from exchange import sender_exchange

from database import customer_authentication
from database import database, customer_dao, customer_basket_doa
from utilities import event, error_wrapper


class customer_service(rpc_server.rpc_server):
    def __init__(self, rabbitmq_params: object, rpc_queue_name: str,
                 notification_exchange_name: str, notification_exchange_type: str,
                 logging_exchange_name: str, logging_exchange_type: str):
        super().__init__(rabbitmq_params, rpc_queue_name)

        if os.environ['DEBUG_FLAG'] == 'True':
            self.DEBUG_FLAG = True
        else:
            self.DEBUG_FLAG = False

        self.notification_exchange_name = notification_exchange_name
        self.logging_exchange_name = logging_exchange_name
        self.logging_exchange_type = logging_exchange_type
        self.notification_exchange_type = notification_exchange_type

        self._postgreSQL_db = self.__customer_db_initialization()

        self.current_customer = None
        self.current_customer_basket = None

    @property
    def notification_exchange_name(self):
        return self._notification_exchange_name

    @notification_exchange_name.setter
    def notification_exchange_name(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ notification exchange name MUST be a string.")
        if not value:
            raise ValueError("RabbitMQ notification exchange name cannot be empty string.")
        self._notification_exchange_name = value

    @property
    def notification_exchange_type(self):
        return self._notification_exchange_type

    @notification_exchange_type.setter
    def notification_exchange_type(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ notification exchange type MUST be a string.")
        if not value:
            raise ValueError("RabbitMQ notification exchange type cannot be empty string.")
        self._notification_exchange_type = value

    @property
    def logging_exchange_name(self):
        return self._logging_exchange_name

    @logging_exchange_name.setter
    def logging_exchange_name(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ logging exchange name MUST be a string.")
        if not value:
            raise ValueError("RabbitMQ logging exchange name cannot be empty string.")
        self._logging_exchange_name = value

    @property
    def logging_exchange_type(self):
        return self._logging_exchange_type

    @logging_exchange_type.setter
    def logging_exchange_type(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ logging exchange type MUST be a string.")
        if not value:
            raise ValueError("RabbitMQ logging exchange type cannot be empty string.")
        self._logging_exchange_type = value

    def __customer_db_initialization(self):
        _postgreSQL_db = database.postgreSQL_database(username=os.environ['POSTGRES_USER'],
                                                      password=os.environ['POSTGRES_PASSWORD'],
                                                      database_name=os.environ['POSTGRES_DB'])
        _postgreSQL_db.drop_schema()
        _postgreSQL_db.create_schema()

        return _postgreSQL_db

    def __notification_msg_sender(self, required_action, payload, **kwargs):
        notification_message = event.notification_event(required_action=required_action, payload=payload)

        for key, value in kwargs.items():
            setattr(notification_message, key, value)

        with sender_exchange.sender_exchange(self.rabbitmq_parameters,
                                             self.notification_exchange_type,
                                             self.notification_exchange_name) as notification_sender:
            try:
                notification_sender('notification.customer', notification_message('json'))
            except Exception as err:
                _error_wrapper = error_wrapper.error_wrapper(err)
                self.__customer_service_log_sender(log_severity='error', payload=_error_wrapper.to_json(),
                                                   message='Notification Sender')

    def __customer_service_log_sender(self, log_severity, **kwargs):
        """

        :type log_severity: str
        """

        log_message = event.log_event(log_severity)

        for key, value in kwargs.items():
            setattr(log_message, key, value)

        with sender_exchange.sender_exchange(self.rabbitmq_parameters,
                                             self.logging_exchange_type,
                                             self.logging_exchange_name) as log_msg_sender:
            try:
                log_msg_sender(log_severity, log_message('json'))
            except Exception as err:
                print(str(err))
                exit(1)

    def message_body_analyzer(self, **kwargs):
        for key, value in kwargs.items():
            if key == 'message_body':
                message_body = value

        message_body_dict = ast.literal_eval(message_body.decode('utf-8'))

        response = json.dumps({})

        if self.DEBUG_FLAG:
            self.__customer_service_log_sender(log_severity='debug', payload=message_body_dict,
                                               message=message_body_dict.get('type'))

        notification_event_payload = message_body_dict.get('payload')
        notification_event_payload['subject'] = message_body_dict.get('required_action')
        if message_body_dict.get('type') == 'load-customers-info':
            _customer_dao = customer_dao.customer_dao(self._postgreSQL_db.get_session())
            response = _customer_dao.load_customers_from_json_file(
                message_body_dict.get('payload').get('customers-file-path'))

            if response['load_customers_information'] == 'Done Successfully':
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('debug', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       correlation_id=message_body_dict.get('correlation_id'))
            else:
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('error', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       correlation_id=message_body_dict.get('correlation_id'))
        elif message_body_dict.get('required_action') == 'customer-sign-in':
            _customer_authentication = customer_authentication.customer_authentication(
                self._postgreSQL_db.get_session())
            response = _customer_authentication.customer_login(
                customer_username=message_body_dict.get('payload').get('username'),
                customer_password=message_body_dict.get('payload').get('password'))
            if response['customer_sign_in'] == 'Login Was Successful':
                _customer_dao = customer_dao.customer_dao(self._postgreSQL_db.get_session())
                response['payload'] = _customer_dao.get_customer_by_username_json(
                    message_body_dict.get('payload').get('username'))
                self.current_customer = _customer_authentication.get_current_customer()
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('debug', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info='Login Was Successful',
                                                       correlation_id=message_body_dict.get('correlation_id'))
            else:
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('error', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info='Login Failed',
                                                       correlation_id=message_body_dict.get('correlation_id'))
        elif message_body_dict.get('required_action') == 'remove-item-from-basket':
            _customer_basket_doa = customer_basket_doa.customer_basket_doa(self._postgreSQL_db.get_session())
            product_info = message_body_dict.get('payload')['product_information']
            response = _customer_basket_doa.remove_item_from_basket(customer_basket_id=self.current_customer_basket.customer_basket_id,
                                                                    isbn=product_info['ISBN'])
            if response['remove_item_from_basket'] == 'Removing Item from Basket Done Successfully':
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('debug', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info=response['remove_item_from_basket'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
            elif response['remove_item_from_basket'] == 'Removing Item from Basket Failed':
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('error', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info=response['remove_item_from_basket'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
        elif message_body_dict.get('required_action') == 'decrement-item-from-basket':
            _customer_basket_doa = customer_basket_doa.customer_basket_doa(self._postgreSQL_db.get_session())
            product_info = message_body_dict.get('payload')['product_information']
            response = _customer_basket_doa.decrement_item_from_basket(customer_basket_id=self.current_customer_basket.customer_basket_id,
                                                                    isbn=product_info['ISBN'])
            if response['decrement_item_from_basket'] == 'Decrementing Item from Basket Done Successfully':
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('debug', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info=response['decrement_item_from_basket'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
            elif response['decrement_item_from_basket'] == 'Decrementing Item from Basket Failed':
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('error', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info=response['decrement_item_from_basket'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
        elif message_body_dict.get('required_action') == 'add-product-to-basket':
            _customer_basket_doa = customer_basket_doa.customer_basket_doa(self._postgreSQL_db.get_session())
            if self.current_customer_basket is None:
                self.current_customer_basket = _customer_basket_doa.create_basket(self.current_customer)

            product_info = message_body_dict.get('payload')['product_information']
            response = _customer_basket_doa.add_product_to_basket(customer_basket=self.current_customer_basket,
                                                                  author=product_info['Author'],
                                                                  title=product_info['Title'],
                                                                  isbn=product_info['ISBN'],
                                                                  price=product_info['Price'],
                                                                  quantity=product_info['Count'],
                                                                  publisher=product_info['Publisher'])
            if response['add_product_to_basket'] == 'Adding Item to Basket Done Successfully':
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('debug', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info=response['add_product_to_basket'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
            elif response['add_product_to_basket'] == 'Adding Item to Basket Failed':
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('error', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info=response['add_product_to_basket'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
        elif message_body_dict.get('required_action') == 'customer-sign-up':
            _customer_dao = customer_dao.customer_dao(self._postgreSQL_db.get_session())

            response = _customer_dao.add_customer_by_parameters(customer_first_name=message_body_dict.get('payload').get('first_name'),
                                                                customer_last_name=message_body_dict.get('payload').get('last_name'),
                                                                customer_username=message_body_dict.get('payload').get('username'),
                                                                customer_password=message_body_dict.get('payload').get('password'),
                                                                customer_email=message_body_dict.get('payload').get('email'),
                                                                customer_phone_number=message_body_dict.get('payload').get('phone'),
                                                                customer_addresses=message_body_dict.get('payload').get('address'))

            notification_event_payload['info'] = response['customer_sign_up']
            if response['customer_sign_up'] == 'Signed Up Successfully':
                self.__notification_msg_sender(required_action='email-signup',
                                               payload=message_body_dict.get('payload'))
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('debug', payload=response,
                                                       message=message_body_dict.get('customer_sign_up'),
                                                       info=response['customer_sign_up'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
            else:
                self.__notification_msg_sender(required_action='email-signup',
                                               payload=notification_event_payload)
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('error', payload=response,
                                                       message=message_body_dict.get('customer_sign_up'),
                                                       info=response['customer_sign_up'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
        elif message_body_dict.get('required_action') == 'get-current-customer':
            if self.current_customer:
                self.__customer_service_log_sender('info', payload=self.current_customer.to_json(),
                                                   message=message_body_dict.get('type'),
                                                   info='Current Customer Info',
                                                   correlation_id=message_body_dict.get('correlation_id'))
                response = self.current_customer.to_json()
            else:
                response = None
        elif message_body_dict.get('required_action') == 'clear-basket':
            _customer_basket_doa = customer_basket_doa.customer_basket_doa(self._postgreSQL_db.get_session())
            response = _customer_basket_doa.clear_basket(customer_basket_id=self.current_customer_basket.customer_basket_id)
            if response['clear_basket'] == 'Clearing basket done successfully':
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('debug', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info=response['clear_basket'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
            else:
                if self.DEBUG_FLAG:
                    self.__customer_service_log_sender('error', payload=response,
                                                       message=message_body_dict.get('type'),
                                                       info=response['clear_basket'],
                                                       correlation_id=message_body_dict.get('correlation_id'))
        elif message_body_dict.get('type') == 'get-all-user':
            _customer_dao = customer_dao.customer_dao(self._postgreSQL_db.get_session())
            # TODO
            # FIX IT
            # TODO
            response = _customer_dao.add_customer_by_parameters('List of parameters')
            if self.DEBUG_FLAG:
                self.__customer_service_log_sender(log_severity='info', payload=response,
                                                   message=message_body_dict.get('type'))
        else:
            self.__customer_service_log_sender(log_severity='Error', payload=message_body_dict,
                                               message=message_body_dict.get('type'))
            exit(1)

        return json.dumps(response)


def customer_service_main():
    try:
        rabbitmq_config = configparser.ConfigParser()
        rabbitmq_config.read(os.environ['RABBITMQ_CONF'])
    except KeyError:
        print("--> ERROR: The environment variable is not set.")
    except FileNotFoundError:
        print(f" --> ERROR: The file at {os.environ['RABBITMQ_CONF']} was NOT found.")
    except Exception as err:
        print(f" --> ERROR: {err}")

    rabbitmq_params = pika.URLParameters(os.environ['RABBITMQ_URL'])

    _customer_service = customer_service(rabbitmq_params,
                                         rabbitmq_config['RABBITMQ_BROKER']['CUSTOMER_SERVICE_QUEUE'],
                                         rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_NAME'],
                                         rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_TYPE'],
                                         rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_NAME'],
                                         rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_TYPE'])
    print("Info: Calling Customer Service")
    _customer_service()


if __name__ == '__main__':
    customer_service_main()
