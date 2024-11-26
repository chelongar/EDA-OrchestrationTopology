#!/usr/bin/python
import ast
import datetime

from current_customer import get_customer_from_customer_service
from flask import Blueprint, current_app
from flask import render_template, request, redirect, url_for
from flask_login import login_required
from utils.helpers import send_message_to_service

from utilities import event

main_blueprint = Blueprint('main', __name__)


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
        if process_add_to_basket(json_object):
            return redirect(url_for('main.get_list_of_books_in_details'))
        else:
            # TODO: Handle failure case when adding to basket fails
            pass

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


def process_add_to_basket(json_object):
    try:
        product_info = ast.literal_eval(json_object)
    except (ValueError, SyntaxError):
        return False

    event_notification = event.notification_event(required_action='add-product-to-basket',
                                                  payload={'product_information': product_info})

    response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])
    return response.get('message') == 'succeed'
