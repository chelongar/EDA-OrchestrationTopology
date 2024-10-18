import ast
import json
import os
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

    :return:
    """
    if request.method == 'GET':
        '''
        First Step:
        Order Placement - Check if the requested purchase is possible to fulfill or not
        '''
        items_price_list = list()
        basket_data = list()
        try:
            basket_data = get_customer_from_customer_service().get('customer_basket', [])[0]['basket_items']
        except (KeyError, IndexError, TypeError) as err:
            print(err)
            logging_message_sender(log_severity='error', payload={err},
                                   exchange_type=current_app.config['LOGGING_EXCHANGE_TYPE'],
                                   exchange_name=current_app.config['LOGGING_EXCHANGE_NAME'],
                                   message='Error occurred in retrieving basket data')
            if not get_customer_from_customer_service() or not isinstance(get_customer_from_customer_service().get('customer_basket'), list):
                return redirect(url_for("main.get_list_of_books_in_details"))

        if not len(basket_data):
            return redirect(url_for("main.get_list_of_books_in_details"))

        for ITERATOR in range(len(basket_data)):
            event_notification = event.notification_event(required_action='check_item_by_ISBN',
                                                          payload={'ISBN': basket_data[ITERATOR].get('ISBN')})
            response = send_message_to_service(event_notification('json'), current_app.config['INVENTORY_QUEUE'])
            response_payload = json.loads(response['payload'])
            if response_payload['status'] == 'item-does-exist':
                if os.environ['DEBUG_FLAG'] == 'True':
                    logging_message_sender(log_severity='info', payload=response_payload,
                                           exchange_type=current_app.config['LOGGING_EXCHANGE_TYPE'],
                                           exchange_name=current_app.config['LOGGING_EXCHANGE_NAME'],
                                           message=event_notification('dict')['required_action'])
                items_price_list.append(basket_data[ITERATOR].get('Price'))
            elif response_payload['status'] == 'item-not-available':
                if os.environ['DEBUG_FLAG'] == 'True':
                    logging_message_sender(log_severity='info', payload=response_payload,
                                           exchange_type=current_app.config['LOGGING_EXCHANGE_TYPE'],
                                           exchange_name=current_app.config['LOGGING_EXCHANGE_NAME'],
                                           message=event_notification('dict')['required_action'])
                return render_template('order_report_failure.html', message='Requested Item Is Not Available')
            elif response_payload['status'] == 'item-does-not-exist':
                if os.environ['DEBUG_FLAG'] == 'True':
                    logging_message_sender(log_severity='info', payload=response_payload,
                                           exchange_type=current_app.config['LOGGING_EXCHANGE_TYPE'],
                                           exchange_name=current_app.config['LOGGING_EXCHANGE_NAME'],
                                           message=event_notification('dict')['required_action'])
                return render_template('order_report_failure.html', message='Requested Item Does Not Exist')
            elif response_payload['status'] == {}:
                if os.environ['DEBUG_FLAG'] == 'True':
                    logging_message_sender(log_severity='info', payload=response_payload,
                                           exchange_type=current_app.config['LOGGING_EXCHANGE_TYPE'],
                                           exchange_name=current_app.config['LOGGING_EXCHANGE_NAME'],
                                           message=event_notification('dict')['required_action'])
                return render_template('order_report_failure.html', message='Invalid Request')
            else:
                return "FAILURE"

        for item in basket_data:
            del item['Count']

        count_dict = defaultdict(int)
        for _item in basket_data:
            # Convert the dictionary to a tuple of sorted items, so it's hashable
            count_dict[tuple(sorted(_item.items()))] += 1

        _basket_data = []
        for _item, count in count_dict.items():
            unique_dict = dict(_item)
            unique_dict['Orders Count'] = count
            _basket_data.append(unique_dict)

        return render_template('customer_basket.html', data=_basket_data,
                               total_price=str(sum(int(_price) for _price in items_price_list)))

    elif request.method == 'POST':
        if request.form.get('action_type') == 'remove':
            return redirect(url_for("basket.remove_item_from_basket",
                                    item_information=ast.literal_eval(request.form.get('json_object'))))
        elif request.form.get('action_type') == 'decrease':
            return redirect(url_for("basket.decrement_item_from_basket",
                                    item_information=ast.literal_eval(request.form.get('json_object'))))
        elif request.form.get('submit_order'):
            return redirect(url_for("payment.payment"))
        elif request.form.get('get_list_of_items'):
            return redirect(url_for("main.get_list_of_books_in_details"))
        else:
            return request.form.get('action_type')


@basket_blueprint.route('/remove_item_from_basket/<item_information>', methods=['POST', 'GET'])
@login_required
def remove_item_from_basket(item_information):
    if request.method == "GET":
        event_notification = event.notification_event(required_action='remove-item-from-basket',
                                                      payload={
                                                          'product_information': ast.literal_eval(item_information)})

        response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])
        if response['message'] == 'succeed':
            basket_data = get_customer_from_customer_service().get('customer_basket')[0].get('basket_items')
            if not len(basket_data):
                return redirect(url_for("main.get_list_of_books_in_details"))

            return redirect(url_for("basket.customer_basket"))
        elif response['message'] == 'failed':
            return response['payload']
    else:
        return redirect(url_for("main.get_list_of_books_in_details"))


@basket_blueprint.route('/decrement_item_from_basket/<item_information>', methods=['POST', 'GET'])
@login_required
def decrement_item_from_basket(item_information):
    if request.method == "GET":
        event_notification = event.notification_event(required_action='decrement-item-from-basket',
                                                      payload={
                                                          'product_information': ast.literal_eval(item_information)})

        response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])
        if response['message'] == 'succeed':
            basket_data = get_customer_from_customer_service().get('customer_basket')[0].get('basket_items')
            if not len(basket_data):
                return redirect(url_for("main.get_list_of_books_in_details"))

            return redirect(url_for("basket.customer_basket"))
        elif response['message'] == 'failed':
            return response['payload']
    else:
        return redirect(url_for("main.get_list_of_books_in_details"))
