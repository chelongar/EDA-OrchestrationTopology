import ast
import json
from collections import defaultdict

from current_customer import get_customer_from_customer_service
from flask import Blueprint, current_app
from flask import render_template, request, redirect, url_for
from flask_login import login_required
from utils.helpers import send_message_to_service, logging_message_sender

from utilities import event

basket_blueprint = Blueprint('basket', __name__)


@basket_blueprint.route('/customer_basket', methods=['GET', 'POST'])
@login_required
def customer_basket():
    """
    Handle the customer basket actions: display basket and manage item actions.
    """
    if request.method == 'GET':
        return handle_get_basket()

    elif request.method == 'POST':
        return handle_post_basket()


def handle_get_basket():
    """
    Handle GET request for the customer basket.
    """
    items_price_list = []
    basket_data = fetch_basket_data()

    if not basket_data:
        return redirect(url_for("main.get_list_of_books_in_details"))

    for item in basket_data:
        response_payload = check_item_availability(item)
        if response_payload:
            status = response_payload['status']
            if status == 'item-does-exist':
                items_price_list.append(item.get('Price'))
            else:
                return handle_item_not_available(status)

    cleaned_basket_data = prepare_basket_data(basket_data)

    return render_template('customer_basket.html', data=cleaned_basket_data,
                           total_price=str(sum(int(price) for price in items_price_list)))


def handle_post_basket():
    """
    Handle POST request for the customer basket.
    """
    action_type = request.form.get('action_type')

    if action_type == 'remove':
        return redirect(url_for("basket.remove_item_from_basket",
                                item_information=ast.literal_eval(request.form.get('json_object'))))
    elif action_type == 'decrease':
        return redirect(url_for("basket.decrement_item_from_basket",
                                item_information=ast.literal_eval(request.form.get('json_object'))))
    elif request.form.get('submit_order'):
        return redirect(url_for("payment.payment"))
    elif request.form.get('get_list_of_items'):
        return redirect(url_for("main.get_list_of_books_in_details"))
    else:
        return action_type


def fetch_basket_data():
    """
    Fetch the basket data from the customer service.
    """
    try:
        response = get_customer_from_customer_service().get('customer_basket', [])
        return response[0]['basket_items'] if response else []
    except (KeyError, IndexError, TypeError) as err:
        logging_message_sender(log_severity='error', payload={err},
                               exchange_type=current_app.config['LOGGING_EXCHANGE_TYPE'],
                               exchange_name=current_app.config['LOGGING_EXCHANGE_NAME'],
                               message='Error occurred in retrieving basket data')
        return []


def check_item_availability(item):
    """
    Check if an item exists in the inventory.
    """
    event_notification = event.notification_event(required_action='check_item_by_ISBN',
                                                  payload={'ISBN': item.get('ISBN')})
    response = send_message_to_service(event_notification('json'), current_app.config['INVENTORY_QUEUE'])

    logging_message_sender('debug', current_app.config['LOGGING_EXCHANGE_TYPE'],
                           current_app.config['LOGGING_EXCHANGE_NAME'], check_item_by_ISBN_response=response['message'])

    return json.loads(response['payload'])


def handle_item_not_available(status):
    """
    Handle cases where the item is not available or does not exist.
    """
    error_messages = {
        'item-not-available': 'Requested Item Is Not Available',
        'item-does-not-exist': 'Requested Item Does Not Exist',
        '': 'Invalid Request',
    }

    if status in error_messages:
        return render_template('order_report_failure.html', message=error_messages[status])

    return "FAILURE"


def prepare_basket_data(basket_data):
    """
    Prepare basket data by counting unique items and their occurrences.
    """
    for item in basket_data:
        del item['Count']  # Remove the Count key as specified

    count_dict = defaultdict(int)
    for item in basket_data:
        count_dict[tuple(sorted(item.items()))] += 1

    return [{**dict(item), 'Orders Count': count} for item, count in count_dict.items()]
     


@basket_blueprint.route('/remove_item_from_basket/<item_information>', methods=['POST', 'GET'])
@login_required
def remove_item_from_basket(item_information):
    if request.method == "GET":
        return handle_item_removal(item_information)
    return redirect(url_for("main.get_list_of_books_in_details"))


def handle_item_removal(item_information):
    event_notification = event.notification_event(required_action='remove-item-from-basket',
                                                  payload={'product_information': ast.literal_eval(item_information)})

    response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])

    logging_message_sender('debug', current_app.config['LOGGING_EXCHANGE_TYPE'],
                           current_app.config['LOGGING_EXCHANGE_NAME'],
                           remove_item_from_basket_response=response['message'])

    if response['message'] == 'succeed':
        return handle_successful_removal()
    elif response['message'] == 'failed':
        return response['payload']

    return redirect(url_for("main.get_list_of_books_in_details"))


def handle_successful_removal():
    basket_data = get_customer_from_customer_service().get('customer_basket')[0].get('basket_items')
    if not basket_data:
        return redirect(url_for("main.get_list_of_books_in_details"))
    return redirect(url_for("basket.customer_basket"))


@basket_blueprint.route('/decrement_item_from_basket/<item_information>', methods=['POST', 'GET'])
@login_required
def decrement_item_from_basket(item_information):
    if request.method != "GET":
        # Redirect if the request method is not GET
        return redirect(url_for("main.get_list_of_books_in_details"))

    # Parse the item information and create the event notification
    try:
        product_info = ast.literal_eval(item_information)
    except (ValueError, SyntaxError) as e:
        return "Invalid item information format.", 400

    event_notification = event.notification_event(required_action='decrement-item-from-basket',
                                                  payload={'product_information': product_info})
    response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])

    logging_message_sender('debug', current_app.config['LOGGING_EXCHANGE_TYPE'],
                           current_app.config['LOGGING_EXCHANGE_NAME'],
                           decrement_item_from_basket_response=response['message'])

    if response.get('message') == 'succeed':
        # Retrieve the customer's basket data
        basket_data = get_customer_from_customer_service().get('customer_basket', [{}])[0].get('basket_items', [])

        # Redirect based on whether the basket has any items left
        if not basket_data:
            return redirect(url_for("main.get_list_of_books_in_details"))

        return redirect(url_for("basket.customer_basket"))

    # Handle failure response
    if response.get('message') == 'failed':
        return response.get('payload', "An error occurred while processing your request."), 500

    # Catch-all for unexpected response structures
    current_app.logger.warning(f"Unexpected response from service: {response}")
    return "Unexpected response from the service.", 500
