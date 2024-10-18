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
    if request.method == "POST":
        if 'get_books_list' in request.form and request.form['get_books_list'] == 'List of Books':
            return redirect(url_for("main.get_list_of_books_in_details"))
        else:
            pass
    return render_template('welcome_page.html', year=datetime.datetime.now().year)


@main_blueprint.route('/list_in_details', methods=['GET', 'POST'])
@login_required
def get_list_of_books_in_details():
    if request.method == "POST":
        if request.form.get('json_object'):
            json_object = request.form.get('json_object')
            event_notification = event.notification_event(required_action='add-product-to-basket',
                                                          payload={'product_information': ast.literal_eval(json_object)})

            response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])
            if response['message'] == 'succeed':
                return redirect(url_for("basket.customer_basket"))

            # TODO
            # Check The Failure
            # TODO

        if request.form.get('basket_items'):
            return redirect(url_for("basket.customer_basket"))
        elif request.form.get('return_home'):
            return redirect(url_for("main.welcome_page"))
        else:
            pass

    elif request.method == "GET":
        event_notification = event.notification_event(required_action='get-list-of-items',
                                                      payload={'info': 'List of All Items in Database'})

        response = send_message_to_service(event_notification('json'), current_app.config['INVENTORY_QUEUE'])
        if response['message'] == 'succeed':
            return render_template('list_of_books_in_details.html', data=response['payload'])
        elif response['payload'] == 'failed':
            return response['payload']
