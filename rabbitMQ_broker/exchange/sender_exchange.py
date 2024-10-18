#!/usr/bin/python

import pika

class sender_exchange(object):
    def __init__(self, rabbitmq_params: object, exchange_type: str, exchange_name: str):
        """
        Exchange - Sender

        :param exchange_name: RabbitMQ exchange name

        Link: https://www.rabbitmq.com/tutorials/tutorial-five-python.html
        """

        self.rabbitmq_parameters = rabbitmq_params
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type

    @property
    def exchange_name(self):
        return self._exchange_name

    @exchange_name.setter
    def exchange_name(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ exchange name must be a string.")
        if not value:
            raise ValueError("RabbitMQ exchange name cannot be empty.")
        self._exchange_name = value

    @property
    def exchange_type(self):
        return self._exchange_type

    @exchange_type.setter
    def exchange_type(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ exchange type must be a string.")
        if not value:
            raise ValueError("RabbitMQ exchange type cannot be empty.")
        self._exchange_type = value

    @property
    def rabbitmq_parameters(self):
        return self._rabbitmq_parameters

    @rabbitmq_parameters.setter
    def rabbitmq_parameters(self, value):
        if not isinstance(value, object):
            raise ValueError("RabbitMQ Parameter MUST be valid object.")

        self._rabbitmq_parameters = value

    def __enter__(self):
        self.connection = pika.BlockingConnection(self.rabbitmq_parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__close()

    def __call__(self, routing_key: str, message: str):
        """
        Call method to send a message by exchange

        :param routing_key:   RabbitMQ routing key
        :param message:             Message to send
        """

        # TODO
        # Use validation for them.
        # TODO
        if isinstance(routing_key, str) and routing_key != '':
            pass
        else:
            print('Routing Key is not valid: ', routing_key)
            exit(1)

        if isinstance(message, str) and message != '':
            self.message = message
        else:
            print('Message is not valid: ', message)
            exit(1)

        self.channel.basic_publish(exchange=self.exchange_name, routing_key=routing_key, body=self.message)

        if __debug__:
            print("Exchange Sender- Message sent: %r" % self.message)

        # Does it correct?
        self.connection.close()

    def __close(self):
        if self.channel and self.channel.is_open:
            self.channel.close()

        if self.connection and self.connection.is_open:
            self.connection.close()
