import json
import os
from functools import wraps

import pika
from RPC import rpc_client
from exchange import sender_exchange
from flask import redirect, url_for
from flask_login import current_user

from utilities import event, error_wrapper


def logout_required(route_function):
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('main.welcome_page'))
        return route_function(*args, **kwargs)
    return decorated_function


def logging_message_sender(log_severity, exchange_type, exchange_name, **kwargs):
    """

    :param exchange_name:   Logging exchange name
    :param exchange_type:   Type of logging exchange
    :type log_severity:     str
    """
    rabbitmq_parameters = pika.URLParameters(os.environ['RABBITMQ_URL'])

    log_message = event.LogEvent(log_severity)

    for key, value in kwargs.items():
        setattr(log_message, key, value)

    with sender_exchange.sender_exchange(rabbitmq_parameters, exchange_type, exchange_name) as log_msg_sender:
        try:
            log_msg_sender(log_severity, log_message('json'))
        except Exception as err:
            print(str(err))


def send_message_to_service(notification: dict, queue_name: str) -> dict:
    """

    :param queue_name:      Queue NAme
    :param notification:    Json to send
    :return: Response       from broker or failure message
    :rtype: dict
    """
    response = dict()
    with rpc_client.rpc_client(pika.URLParameters(os.environ['RABBITMQ_URL']), queue_name) as mediator_client:
        try:
            response['payload'] = json.loads(mediator_client(notification))
            response['message'] = 'succeed'
            return response
        except ValueError as err:
            _error_wrapper = error_wrapper.error_wrapper(err)
            # TODO
            # FIX IT
            # TODO
            logging_message_sender(log_severity='error', payload=_error_wrapper.to_json(),
                                   message=notification.get('type'))
            response['payload'] = _error_wrapper.to_json()
            response['message'] = 'failed'
            return response


def notification_msg_sender(required_action, exchange_type, exchange_name,  payload, **kwargs):
    notification_message = event.NotificationEvent(required_action=required_action, payload=payload)

    for key, value in kwargs.items():
        setattr(notification_message, key, value)

    with sender_exchange.sender_exchange(pika.URLParameters(os.environ['RABBITMQ_URL']),
                                         exchange_type, exchange_name) as notification_sender:
        try:
            notification_sender('notification.mediator', notification_message('json'))
        except Exception as err:
            _error_wrapper = error_wrapper.error_wrapper(err)
            logging_message_sender(log_severity='error', payload=_error_wrapper.to_json(),
                                   exchange_name=exchange_name, exchange_type=exchange_type,
                                   message='Notification Sender')
