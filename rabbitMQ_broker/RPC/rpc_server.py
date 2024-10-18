#!/usr/bin/python

import pika
import abc


class rpc_server(object):
    def __init__(self, rabbitmq_params: object, rpc_queue_name: str):
        """
        RPC RabbitMQ server

        :param rpc_queue_name: RabbitMQ queue name
        """

        if isinstance(rabbitmq_params, object):
            self.rabbitmq_parameters = rabbitmq_params
        else:
            print('Pika object is not valid: ', rabbitmq_params)
            exit(1)

        if isinstance(rpc_queue_name, str):
            self.rpc_queue_name = rpc_queue_name
        else:
            print('Routing Key is not valid: ', rpc_queue_name)
            exit(1)

        self.connection = pika.BlockingConnection(self.rabbitmq_parameters)

        self.channel = self.connection.channel()

        self.channel.queue_declare(queue=self.rpc_queue_name)

        self.channel.basic_qos(prefetch_count=1)

    @abc.abstractmethod
    def message_body_analyzer(self, **kwargs):
        pass

    def __request_service(self, ch, method, props, body):

        response = self.message_body_analyzer(message_body=body)

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=response)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __call__(self):
        self.channel.basic_consume(queue=self.rpc_queue_name,
                                   on_message_callback=self.__request_service)

        self.channel.start_consuming()
