#!/usr/bin/python
import json

from current_customer import get_customer_from_customer_service
from flask import Blueprint, current_app
from flask import render_template, request, redirect, url_for
from flask_login import login_required

from utilities import event
from utils.helpers import send_message_to_service, logging_message_sender, notification_msg_sender

payment_blueprint = Blueprint('payment', __name__)


def payment_steps_manager(notification_payload, payment_payload, book_isbns):
    event_notification = event.notification_event(required_action='paypal-payment', payload=payment_payload)

    response = send_message_to_service(event_notification('json'), current_app.config['PAYMENT_QUEUE'])

    logging_message_sender('debug', current_app.config['LOGGING_EXCHANGE_TYPE'],
                           current_app.config['LOGGING_EXCHANGE_NAME'], payment_service_response=response)
    if response.get('payload')['status'] == 'success':
        # Send an invoice to customer
        notification_msg_sender('email-invoice', current_app.config['NOTIFICATION_EXCHANGE_TYPE'],
                                current_app.config['NOTIFICATION_EXCHANGE_NAME'], notification_payload)

        _event_notification = event.notification_event(required_action='clear-basket', payload={})
        response = send_message_to_service(_event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])
        if response['message'] == 'succeed':
            for isbn in book_isbns:
                inventory_event_notification = event.notification_event(required_action='order_item_with_ISBN',
                                                                        payload={'ISBN': isbn})
                inventory_response = send_message_to_service(inventory_event_notification('json'),
                                                             current_app.config['INVENTORY_QUEUE'])
                if inventory_response['message'] == 'succeed':
                    pass
                else:
                    # TODO
                    # Should be redirected to failure page
                    # TODO
                    pass
        elif response['message'] == 'failed':
            return response['payload']
        return redirect(url_for("main.welcome_page"))
    else:
        # TODO
        # Failure
        # TODO
        return response


@payment_blueprint.route('/payment', methods=['POST', 'GET'])
@login_required
def payment():
    items_price_list = list()
    basket_data = get_customer_from_customer_service().get('customer_basket')[0]['basket_items']
    for ITERATOR in range(len(basket_data)):
        items_price_list.append(basket_data[ITERATOR].get('Price'))

    book_isbns = list()
    for item in basket_data:
        book_isbns.append(item['ISBN'])

    for item in basket_data:
        del item['Count']
        del item['Publisher']
        del item['ISBN']
        del item['Author']

    total_price = str(sum(int(_price) for _price in items_price_list))

    notification_payload = {'purchased_items': basket_data,
                            'total_price': total_price,
                            'email': get_customer_from_customer_service()['email'],
                            'first_name': get_customer_from_customer_service()['first_name'],
                            'last_name': get_customer_from_customer_service()['last_name']}

    payment_payload = {'basket_data': basket_data,
                       'total_price': total_price}

    if request.method == "POST":
        if request.form.get('paypal'):
            notification_payload['subject'] = 'paypal-payment'
            notification_payload['info'] = 'Payment with Paypal is requested'

            return payment_steps_manager(notification_payload=notification_payload,
                                         payment_payload=payment_payload, book_isbns=book_isbns)
        elif request.form.get('mastercard'):
            notification_payload['subject'] = 'mastercard-payment'
            notification_payload['info'] = 'Payment with Mastercard is requested'

            return payment_steps_manager(notification_payload=notification_payload,
                                         payment_payload=payment_payload, book_isbns=book_isbns)
        if request.form.get('visa'):
            notification_payload['subject'] = 'visa-payment'
            notification_payload['info'] = 'Payment with visa card is requested'

            return payment_steps_manager(notification_payload=notification_payload,
                                         payment_payload=payment_payload, book_isbns=book_isbns)
        elif request.form.get('return_home'):
            return redirect(url_for("main.welcome_page"))
        else:
            pass

    elif request.method == "GET":
        return render_template('payment.html', data=basket_data, total_price=total_price)
