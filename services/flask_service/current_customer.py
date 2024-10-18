from flask_login import UserMixin

from utils.helpers import send_message_to_service
from utilities import event


def get_customer_from_customer_service():
    event_notification = event.notification_event(required_action='get-current-customer', payload={})

    response = send_message_to_service(event_notification('json'), 'rpc_queue_customer')
    if response['message'] == 'succeed':
        return response['payload']
    elif response['payload'] == 'failed':
        return response['payload']


class current_customer(UserMixin):
    def __init__(self, _id, _username):
        self.id = _id
        self.username = _username

    @staticmethod
    def from_json(_customer_data):
        return current_customer(_customer_data['customer_id'], _customer_data['username'])

    @staticmethod
    def get_from_customer_service(_id):
        customer_data = get_customer_from_customer_service()
        return current_customer.from_json(customer_data) if customer_data else None
