#!/usr/bin/env python
import ast
import configparser
import json
import os

import pika
from exchange import receiver_exchange


class logging_service(receiver_exchange.receiver_exchange):
    def message_body_analyzer(self, **kwargs):

        for key, value in kwargs.items():
            if key == 'message_body':
                message_body = value
            elif key == 'broker_method':
                broker_method = value

        _message_body = ast.literal_eval(str(json.loads(message_body)))

        _message_body['binding_key'] = broker_method.routing_key

        _message_body['exchange_name'] = broker_method.exchange

        print(str(json.dumps(_message_body)))

        return _message_body.get('message')


def logging_service_main():
    try:
        config = configparser.ConfigParser()
        config.read(os.environ['RABBITMQ_CONF'])
    except KeyError:
        print("--> ERROR: The environment variable is not set.")
    except FileNotFoundError:
        print(f" --> ERROR: The file at {os.environ['RABBITMQ_CONF']} was NOT found.")
    except Exception as err:
        print(f" --> ERROR: {err}")

    rabbitmq_params = pika.URLParameters(os.environ['RABBITMQ_URL'])

    _logging_service = logging_service(rabbitmq_params,
                                       [item.strip() for item in config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_ROUTING_KEYS'].split(',')],
                                       config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_TYPE'],
                                       config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_NAME'])
    _logging_service()


if __name__ == '__main__':
    logging_service_main()
