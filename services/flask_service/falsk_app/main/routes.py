#!/usr/bin/python
import ast
import datetime
from enum import Enum

from flask import Blueprint, current_app
from flask import render_template, request, redirect, url_for
from flask_login import login_required

from utils.helpers import send_message_to_service
from utilities import event
from current_customer import get_customer_from_customer_service

main_blueprint = Blueprint('main', __name__)


class validation_results(Enum):
    ADDING_SUCCEED = "adding_succeed"
    ADDING_FAILED = "adding_failed"
    INVALID_INPUT = "invalid_input"
    ADDING_PREVENTED = "adding_prevented"


@main_blueprint.route('/home', methods=['POST', 'GET'])
@login_required
def welcome_page():
    if request.method == 'POST' and request.form.get('get_books_list') == 'List of Books':
        return redirect(url_for('main.get_list_of_books_in_details'))

    # Render the welcome page for GET requests or other cases
    current_year = datetime.datetime.now().year
    return render_template('welcome_page.html', year=current_year)


@main_blueprint.route('/list_in_details', methods=['GET', 'POST'])
@login_required
def get_list_of_books_in_details():
    if request.method == "POST":
        return handle_post_request()
    elif request.method == "GET":
        return handle_get_request()
    return '', 405  # Method Not Allowed


def handle_post_request():
    json_object = request.form.get('json_object')
    if json_object:
        add_to_list_result = process_add_to_basket(json_object)
        if add_to_list_result == validation_results.ADDING_SUCCEED:
            return redirect(url_for('main.get_list_of_books_in_details'))
        elif add_to_list_result == validation_results.ADDING_FAILED:
            return render_template('order_report_failure.html', message='Adding Failed',
                                   year=datetime.datetime.now().year)
        elif add_to_list_result == validation_results.ADDING_PREVENTED:
            return render_template('order_report_failure.html',
                                   message='You can not order more than 3 copies from this book',
                                   year=datetime.datetime.now().year)
        elif add_to_list_result == validation_results.INVALID_INPUT:
            return render_template('order_report_failure.html', message='Invalid Product Information',
                                   year=datetime.datetime.now().year)

    if request.form.get('basket_items'):
        return redirect(url_for("basket.customer_basket"))

    if request.form.get('return_home'):
        return redirect(url_for("main.welcome_page"))

    return '', 400  # Bad Request


def handle_get_request():
    event_notification = event.notification_event(required_action='get-list-of-items',
                                                  payload={'info': 'List of All Items in Database'})

    response = send_message_to_service(event_notification('json'), current_app.config['INVENTORY_QUEUE'])
    if response.get('message') == 'succeed':
        return render_template('list_of_books_in_details.html', data=response.get('payload'))
    if response.get('payload') == 'failed':
        return response.get('payload'), 500  # Internal Server Error

    return '', 400  # Bad Request


def product_count_in_basket(product_isbn):
    customer_data = get_customer_from_customer_service().get('customer_basket', [])
    basket_items = customer_data[0]['basket_items'] if customer_data else []

    # Return 0 if basket is not created yet
    if not basket_items:
        return 0

    return sum(1 for item in basket_items if item.get('ISBN') == product_isbn)


def process_add_to_basket(json_object):
    try:
        product_info = ast.literal_eval(json_object)
    except (ValueError, SyntaxError):
        return validation_results.INVALID_INPUT

    if product_count_in_basket(product_info.get('ISBN')) < 3:
        event_notification = event.notification_event(required_action='add-product-to-basket',
                                                      payload={'product_information': product_info})

        response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])
        if response.get('message') == 'succeed':
            return validation_results.ADDING_SUCCEED
        else:
            return validation_results.ADDING_FAILED
    else:
        return validation_results.ADDING_PREVENTED
