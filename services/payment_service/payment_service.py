#!/usr/bin/python

import ast
import configparser
import json
import os

import pika
from RPC import rpc_server
from exchange import sender_exchange

from utilities import event


def process_mastercard_payment(card_details, amount):
    # TODO
    # Should be implemented
    # TODO
    return {"status": "success", "message": "Mastercard payment processed"}


def process_visa_payment(card_details, amount):
    # TODO
    # Should be implemented
    # TODO
    return {"status": "success", "message": "Visa payment processed"}


def process_paypal_payment(paypal_details, amount):
    # TODO
    # Should be implemented
    # TODO
    return {"status": "success", "message": "PayPal payment processed"}


class payment_handler(rpc_server.rpc_server):
    def __init__(self, rabbitmq_params, queue_name: str,
                 notification_exchange_name: str, notification_exchange_type: str,
                 logging_exchange_name: str, logging_exchange_type: str):
        super().__init__(rabbitmq_params, queue_name)

        self.DEBUG_FLAG = os.environ.get('DEBUG_FLAG', 'False') == 'True'
        print(self.DEBUG_FLAG)

        self.notification_exchange_name = notification_exchange_name
        self.notification_exchange_type = notification_exchange_type
        self.logging_exchange_name = logging_exchange_name
        self.logging_exchange_type = logging_exchange_type

    @property
    def notification_exchange_name(self):
        return self._notification_exchange_name

    @notification_exchange_name.setter
    def notification_exchange_name(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ notification exchange name MUST be a string.")
        if not value:
            raise ValueError("RabbitMQ notification exchange name CAN NOT be empty string.")
        self._notification_exchange_name = value

    @property
    def notification_exchange_type(self):
        return self._notification_exchange_type

    @notification_exchange_type.setter
    def notification_exchange_type(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ notification exchange type MUST be a string.")
        if not value:
            raise ValueError("RabbitMQ notification exchange type CAN NOT be empty string.")
        self._notification_exchange_type = value

    @property
    def logging_exchange_name(self):
        return self._logging_exchange_name

    @logging_exchange_name.setter
    def logging_exchange_name(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ logging exchange name MUST be a string.")
        if not value:
            raise ValueError("RabbitMQ logging exchange name CAN NOT be empty string.")
        self._logging_exchange_name = value

    @property
    def logging_exchange_type(self):
        return self._logging_exchange_type

    @logging_exchange_type.setter
    def logging_exchange_type(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ logging exchange type MUST be a string.")
        if not value:
            raise ValueError("RabbitMQ logging exchange type CAN NOT be empty string.")
        self._logging_exchange_type = value

    def __payment_log_sender(self, log_severity: str, **kwargs):
        """

        :type log_severity: str
        :type message:      dict
        :param message:     Message to send to Logging Service and Logging Service
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
        message_body = kwargs.get('message_body', None)

        if message_body:
            # Parse the message body to dictionary
            message_body_dict = ast.literal_eval(message_body.decode('utf-8'))
            notification_event_payload = message_body_dict.get('payload', {})
            required_action = message_body_dict.get('required_action')
            notification_event_payload['subject'] = required_action

            log_payment_info = lambda action: self.__payment_log_sender('info',
                                                                        payload=notification_event_payload,
                                                                        message=action,
                                                                        info=f"Payment with {action.split('-')[0].capitalize()} is requested",
                                                                        correlation_id=message_body_dict.get('correlation_id')
                                                                        ) if self.DEBUG_FLAG == 'True' else None

            # Payment processors mapped to required_action
            payment_processors = {
                'paypal-payment': lambda: process_paypal_payment(None,
                                                                 amount=notification_event_payload.get('total_price')),
                'visa-payment': lambda: process_visa_payment(None,
                                                             amount=notification_event_payload.get('total_price')),
                'mastercard-payment': lambda: process_mastercard_payment(None,
                                                                         amount=notification_event_payload.get('total_price'))
            }

            # Execute the payment processor if action is valid, otherwise return failure message
            if required_action in payment_processors:
                log_payment_info(required_action)
                return json.dumps(payment_processors[required_action]())
            else:
                return json.dumps({"status": "failed", "message": "payment failed"})


def payment_handler_main():
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

    _payment_handler = payment_handler(rabbitmq_params,
                                       rabbitmq_config['RABBITMQ_BROKER']['PAYMENT_QUEUE'],
                                       rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_NAME'],
                                       rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_TYPE'],
                                       rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_NAME'],
                                       rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_TYPE'])
    _payment_handler()


if __name__ == '__main__':
    payment_handler_main()
