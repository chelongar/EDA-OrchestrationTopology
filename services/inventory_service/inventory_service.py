#!/usr/bin/python

import ast
import configparser
import json
import os

import pika
from RPC import rpc_server
from exchange import sender_exchange

from database import database_interface
from utilities import event


class inventory_service(rpc_server.rpc_server):
    def __init__(self, rabbitmq_params: object, rpc_queue_name: str,
                 notification_exchange_name: str, notification_exchange_type: str,
                 logging_exchange_name: str, logging_exchange_type: str, json_file_path: str = None):
        super().__init__(rabbitmq_params, rpc_queue_name)

        self.DEBUG_FLAG = os.environ.get('DEBUG_FLAG', 'False') == 'True'

        self.json_file_path = json_file_path
        self._setup_database()

        self.notification_exchange_name = notification_exchange_name
        self.notification_exchange_type = notification_exchange_type
        self.logging_exchange_name = logging_exchange_name
        self.logging_exchange_type = logging_exchange_type

    def _setup_database(self):
        """Initialize database from the provided JSON file path."""
        if not self.json_file_path:
            self._handle_invalid_json_path("JSON file path is missing.")

        if not isinstance(self.json_file_path, str):
            self._handle_invalid_json_path("Invalid JSON file path type. Expected a string.")

        try:
            self._database_handler = database_interface.database_interface(self.json_file_path)
            self._database_handler.create_db_table()
            self._database_handler.load_data_to_database()
        except (FileNotFoundError, IOError) as e:
            self._handle_invalid_json_path(f"Failed to open JSON file: {e}")

    def _handle_invalid_json_path(self, error_message: str):
        print(f"Error: {error_message}")
        exit(1)

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

    def __inventory_log_sender(self, log_severity, **kwargs):
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

    def message_body_analyzer(self, **kwargs):
        # Extract the message_body from kwargs
        message_body = kwargs.get('message_body', b'').decode('utf-8')

        # Parse the message body
        try:
            message_body_dict = ast.literal_eval(message_body)
        except (ValueError, SyntaxError):
            self.__inventory_log_sender('error',
                                        payload={'error': 'Invalid message body format'},
                                        info='parsing_error')
            return json.dumps({})

        # Log the incoming message in debug mode
        if self.DEBUG_FLAG:
            self.__inventory_log_sender('debug', payload=message_body_dict,
                                        info=message_body_dict.get('required_action', 'unknown'))

        # Map of required actions to corresponding database handler methods
        action_map = {'get-list-of-items': self._database_handler.get_list_of_items,
                      'check_item_by_ISBN': lambda: self._database_handler.check_book_by_id(message_body_dict.get('payload', {}).get('ISBN')),
                      'check_item_by_title': lambda: self._database_handler.check_book_by_title(message_body_dict.get('payload', {}).get('Title')),
                      'get_item_price_by_ISBN': lambda: self._database_handler.get_book_price_by_id(message_body_dict.get('payload', {}).get('ISBN')),
                      'get_item_price_by_title': lambda: self._database_handler.get_book_price_by_title(message_body_dict.get('payload', {}).get('Title')),
                      'order_item_with_ISBN': lambda: self._database_handler.get_book_by_id(message_body_dict.get('payload', {}).get('ISBN')),
                      'order_item_with_title': lambda: self._database_handler.get_book_by_title(message_body_dict.get('payload', {}).get('Title'))
                      }

        # Get the required action
        required_action = message_body_dict.get('required_action')

        # Execute the corresponding action or log an error if action is invalid
        if required_action in action_map:
            response = action_map[required_action]()
            # Log the response in debug mode
            if self.DEBUG_FLAG:
                self.__inventory_log_sender('debug', payload=response, info=message_body_dict.get('type', 'unknown'))
        else:
            self.__inventory_log_sender('error', payload=message_body_dict, info='unknown_action')
            return json.dumps({})

        return json.dumps(response)


def inventory_service_main():
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

    try:
        product_config = configparser.ConfigParser()
        product_config.read(os.environ['PRODUCTS_CONF'])
    except KeyError:
        print("--> ERROR: The environment variable is not set.")
    except FileNotFoundError:
        print(f" --> ERROR: The file at {os.environ['PRODUCTS_CONF']} was NOT found.")
    except Exception as err:
        print(f" --> ERROR: {err}")

    _inventory_service = inventory_service(rabbitmq_params,
                                           rabbitmq_config['RABBITMQ_BROKER']['INVENTORY_QUEUE'],
                                           rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_NAME'],
                                           rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_TYPE'],
                                           rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_NAME'],
                                           rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_TYPE'],
                                           product_config['PRODUCTS']['ITEMS'])
    _inventory_service()


if __name__ == '__main__':
    inventory_service_main()
