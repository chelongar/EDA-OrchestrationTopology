#!/usr/bin/python
from collections import defaultdict

from current_customer import get_customer_from_customer_service
from flask import Blueprint, current_app
from flask import render_template, request, redirect, url_for
from flask_login import login_required
from utils.helpers import send_message_to_service, logging_message_sender, notification_msg_sender

from utilities import event

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
    customer_data = get_customer_from_customer_service()
    basket_data = customer_data.get('customer_basket')[0]['basket_items']

    # Using map and lambda to extract prices and ISBNs
    items_price_list = list(map(lambda _item: _item.get('Price'), basket_data))
    book_isbns = list(map(lambda _item: _item['ISBN'], basket_data))

    # Removing unnecessary fields in basket items
    fields_to_remove = ['Count', 'Publisher', 'ISBN', 'Author']
    for item in basket_data:
        for field in fields_to_remove:
            item.pop(field, None)

    total_price = str(sum(map(int, items_price_list)))

    # Create notification and payment payloads
    notification_payload = {'purchased_items': basket_data,
                            'total_price': total_price,
                            'email': customer_data['email'],
                            'first_name': customer_data['first_name'],
                            'last_name': customer_data['last_name']
                            }

    payment_payload = {'basket_data': basket_data,
                       'total_price': total_price
                       }

    if request.method == "POST":
        payment_methods = {'paypal': 'paypal-payment',
                           'mastercard': 'mastercard-payment',
                           'visa': 'visa-payment'
                           }

        for method, subject in payment_methods.items():
            if request.form.get(method):
                notification_payload.update({'subject': subject,
                                             'info': f'Payment with {method.capitalize()} is requested'})
                return payment_steps_manager(notification_payload=notification_payload,
                                             payment_payload=payment_payload,
                                             book_isbns=book_isbns)

        if request.form.get('return_home'):
            return redirect(url_for("main.welcome_page"))

    elif request.method == "GET":
        count_dict = defaultdict(int)
        for item in basket_data:
            count_dict[tuple(sorted(item.items()))] += 1

        _basket_data = [{**dict(item), 'Orders Count': count} for item, count in count_dict.items()]
        return render_template('payment.html', data=_basket_data, total_price=total_price)

