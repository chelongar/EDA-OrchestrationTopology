#!/usr/bin/python

import pika
import uuid


class rpc_client(object):
    def __init__(self, rabbitmq_params: object, rpc_routing_key: str):
        """
        RPC RabbitMQ client

        :type rabbitmq_params: Pika Object
        :param rpc_routing_key: RabbitMQ RPC routing key
        """

        self.rabbitmq_parameters = rabbitmq_params
        self.rpc_routing_key = rpc_routing_key
        
    @property
    def rpc_routing_key(self):
        return self._rpc_routing_key

    @rpc_routing_key.setter
    def rpc_routing_key(self, value):
        if not isinstance(value, str):
            raise ValueError("RabbitMQ RPC routing key must be a string.")
        if not value:
            raise ValueError("RabbitMQ RPC routing key cannot be empty.")
        self._rpc_routing_key = value

    @property
    def rabbitmq_parameters(self):
        return self._rabbitmq_parameters

    @rabbitmq_parameters.setter
    def rabbitmq_parameters(self, value):
        if not isinstance(value, object):
            raise ValueError("RabbitMQ Parameter MUST be valid object.")

        self._rabbitmq_parameters = value

    def __enter__(self):
        self.response = None
        self.correlation_id = str(uuid.uuid4())

        self.connection = pika.BlockingConnection(self.rabbitmq_parameters)

        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(queue=self.callback_queue,
                                   on_message_callback=self.on_response_method,
                                   auto_ack=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__close()

    def on_response_method(self, ch, method, props, body):
        if __debug__:
            print('Routing Key:', method.routing_key)

        if self.correlation_id == props.correlation_id:
            self.response = body

    def __call__(self, request_message):
        """

        :param request_message: Message to sent by broker
        :return: analyzed response
        """
        self.channel.basic_publish(exchange='',
                                   routing_key=self.rpc_routing_key,
                                   properties=pika.BasicProperties(reply_to=self.callback_queue,
                                                                   correlation_id=self.correlation_id, ),
                                   body=str(request_message))

        while self.response is None:
            self.connection.process_data_events()

        return self.response

    def __close(self):
        if self.channel and self.channel.is_open:
            self.channel.close()

        if self.connection and self.connection.is_open:
            self.connection.close()
