import json
import os
import configparser
from typing import Any

import pika
from RPC import rpc_server
from exchange import sender_exchange
from database import database_interface
from utilities import event


class InventoryService(rpc_server.rpc_server):
    """Inventory service handling product queries and logging via RabbitMQ."""

    def __init__(self,
                 rabbitmq_params: Any,
                 rpc_queue_name: str,
                 notification_exchange_name: str,
                 notification_exchange_type: str,
                 logging_exchange_name: str,
                 logging_exchange_type: str,
                 products_json_path: str = None):
        super().__init__(rabbitmq_params, rpc_queue_name)

        self.DEBUG_FLAG = os.environ.get('DEBUG_FLAG', 'False') == 'True'
        self.products_json_path = products_json_path
        self._setup_database()

        """
        Validate and assign exchange names and types
        """
        self._notification_exchange_name = self._validate_non_empty_str(notification_exchange_name,
                                                                        "Notification exchange name")
        self._notification_exchange_type = self._validate_non_empty_str(notification_exchange_type,
                                                                        "Notification exchange type")
        self._logging_exchange_name = self._validate_non_empty_str(logging_exchange_name,
                                                                   "Logging exchange name")
        self._logging_exchange_type = self._validate_non_empty_str(logging_exchange_type,
                                                                   "Logging exchange type")

    def _validate_non_empty_str(self, value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string.")
        return value

    def _setup_database(self):
        if not self.products_json_path or not isinstance(self.products_json_path, str):
            raise RuntimeError("Invalid or missing JSON file path for product data.")

        try:
            self._database_handler = database_interface.database_interface(self.products_json_path)
            self._database_handler.create_db_table()
            self._database_handler.load_data_to_database()
        except (FileNotFoundError, IOError) as e:
            raise RuntimeError(f"Failed to initialize database: {e}")

    def _send_log(self, log_severity: str, **kwargs):
        log_message = event.LogEvent(log_severity)
        for key, value in kwargs.items():
            setattr(log_message, key, value)

        try:
            with sender_exchange.sender_exchange(self.rabbitmq_parameters,
                                                 self._logging_exchange_type,
                                                 self._logging_exchange_name) as log_sender:
                log_sender(log_severity, log_message('json'))
        except Exception as err:
            print(f"Logging failed: {err}")

    def message_body_analyzer(self, **kwargs):
        raw_body = kwargs.get('message_body', b'').decode('utf-8')

        try:
            message_body_dict = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_log('error', payload={'error': 'Invalid message body format'}, info='parsing_error')
            return json.dumps({})

        if self.DEBUG_FLAG:
            self._send_log('debug', payload=message_body_dict,
                           info=message_body_dict.get('required_action', 'unknown'))

        payload = message_body_dict.get('payload', {})
        action_map = {
            'get-list-of-items': self._database_handler.get_list_of_items,
            'check_item_by_ISBN': lambda: self._database_handler.check_book_by_id(payload.get('ISBN')),
            'check_item_by_title': lambda: self._database_handler.check_book_by_title(payload.get('Title')),
            'get_item_price_by_ISBN': lambda: self._database_handler.get_book_price_by_id(payload.get('ISBN')),
            'get_item_price_by_title': lambda: self._database_handler.get_book_price_by_title(payload.get('Title')),
            'order_item_with_ISBN': lambda: self._database_handler.get_book_by_id(payload.get('ISBN')),
            'order_item_with_title': lambda: self._database_handler.get_book_by_title(payload.get('Title'))
        }

        required_action = message_body_dict.get('required_action')
        if required_action in action_map:
            response = action_map[required_action]()
            if self.DEBUG_FLAG:
                self._send_log('debug', payload=response, info=message_body_dict.get('type', 'unknown'))
            return json.dumps(response)
        else:
            self._send_log('error', payload=message_body_dict, info='unknown_action')
            return json.dumps({})


def load_config(path_env_var: str) -> configparser.ConfigParser:
    path = os.environ.get(path_env_var)
    if not path:
        raise EnvironmentError(f"Environment variable '{path_env_var}' is not set.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at: {path}")

    config = configparser.ConfigParser()
    config.read(path)
    return config


def inventory_service_main():
    try:
        rabbitmq_config = load_config('RABBITMQ_CONF')
        product_config = load_config('PRODUCTS_CONF')
        rabbitmq_params = pika.URLParameters(os.environ['RABBITMQ_URL'])

        _InventoryService = InventoryService(rabbitmq_params,
                                             rabbitmq_config['RABBITMQ_BROKER']['INVENTORY_QUEUE'],
                                             rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_NAME'],
                                             rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_TYPE'],
                                             rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_NAME'],
                                             rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_TYPE'],
                                             product_config['PRODUCTS']['ITEMS'])

        _InventoryService()

    except Exception as e:
        print(f"Failed to start InventoryService: {e}")


if __name__ == '__main__':
    inventory_service_main()
