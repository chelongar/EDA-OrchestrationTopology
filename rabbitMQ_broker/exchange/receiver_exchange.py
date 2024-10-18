#!/usr/bin/python

import abc
import pika


class receiver_exchange(object):
    def __init__(self, rabbitmq_params: object, routing_keys: list, exchange_type: str, exchange_name: str):
        """
        Topic exchange - Receiver

        :param exchange_name: RabbitMQ exchange name
        :param routing_keys: Queue routing key

        Link: https://www.rabbitmq.com/tutorials/tutorial-five-python.html
        """
        if __debug__:
            print("Exchange Receiver- input exchange type: ", exchange_type)
            print("Exchange Receiver- input exchange name: ", exchange_name)
            print("Exchange Receiver- input routing keys list: ", routing_keys)

        if isinstance(rabbitmq_params, object):
            self.rabbitmq_parameters = rabbitmq_params
        else:
            print('Pika object is not valid: ', rabbitmq_params)
            exit(1)

        if isinstance(exchange_name, str) and exchange_name != '':
            self.exchange_name = exchange_name
        else:
            print('Exchange name is not valid: ', exchange_name)
            exit(1)

        if isinstance(routing_keys, list) and routing_keys != []:
            self.routing_keys = routing_keys
        else:
            print('Binding keys is not valid: ', routing_keys)
            exit(1)

        if isinstance(exchange_type, str) and exchange_type != '':
            self.exchange_type = exchange_type
        else:
            print('Exchange type is not valid: ', exchange_type)
            exit(1)

        self.connection = pika.BlockingConnection(self.rabbitmq_parameters)

        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type)

        result = self.channel.queue_declare('', exclusive=True)
        self.queue_name = result.method.queue

        '''
        Assign a queue to each biding key in the list
        '''
        for routing_key in self.routing_keys:
            self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=routing_key)

        if __debug__:
            print('Exchange Receiver- Waiting for message...')

    def __del__(self):
        self.connection.close()
        if __debug__:
            print("Exchange Receiver- Object is destroyed, connection closed")

    @abc.abstractmethod
    def message_body_analyzer(self, message: str):
        pass

    def exchange_callback(self, ch, method, properties, message_body):
        self.message_body_analyzer(message_body=message_body, broker_method=method)

    def __call__(self):
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.exchange_callback, auto_ack=True)

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print('Exchange Receiver- chanel consuming is stopped')
            self.channel.stop_consuming()
