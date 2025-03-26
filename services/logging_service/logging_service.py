import json
import configparser
import os

import pika
from exchange import receiver_exchange


class LoggingService(receiver_exchange.receiver_exchange):
    def message_body_analyzer(self, **kwargs):
        message_body_raw = kwargs.get('message_body', b'').decode('utf-8')
        broker_method = kwargs.get('broker_method', None)

        try:
            message_body = json.loads(message_body_raw)
        except json.JSONDecodeError:
            print("Invalid log message format. Skipping.")
            return

        if broker_method:
            message_body['binding_key'] = broker_method.routing_key
            message_body['exchange_name'] = broker_method.exchange

        print(json.dumps(message_body, indent=2))
        return message_body.get('message')


def logging_service_main():
    try:
        config = configparser.ConfigParser()
        config.read(os.environ['RABBITMQ_CONF'])

        rabbitmq_params = pika.URLParameters(os.environ['RABBITMQ_URL'])
        routing_keys = [item.strip() for item in config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_ROUTING_KEYS'].split(',')]

        _LoggingService = LoggingService(rabbitmq_params,
                                         routing_keys,
                                         config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_TYPE'],
                                         config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_NAME']
        )
        _LoggingService()

    except KeyError as err:
        print(f"Missing environment variable: {err}")
    except FileNotFoundError:
        print(f"Config file not found at: {os.environ.get('RABBITMQ_CONF', 'UNSET')}.")
    except Exception as err:
        print(f"Failed to start LoggingService: {err}")


if __name__ == '__main__':
    logging_service_main()