#!/usr/bin/python
import datetime

from flask import Blueprint, current_app
from flask import jsonify, render_template, request
from utils.helpers import send_message_to_service

from utils.helpers import logout_required
from utilities import event

signup_blueprint = Blueprint('signup', __name__)


@signup_blueprint.route('/customer_sign_up', methods=['POST', 'GET'])
@logout_required
def customer_sign_up():
    if request.method == "POST":
        customer_info = request.form

        if not customer_info:
            return jsonify({'error': 'No data provided'}), 400

        if (not customer_info.get('email') or not customer_info.get('firstname') or not customer_info.get('lastname') or
                not customer_info.get('street') or not customer_info.get('password') or not customer_info.get('username')):
            return jsonify({'error': 'Incomplete registration information'}), 400

        payload = {
            'username': customer_info.get('username'),
            'password': customer_info.get('password'),
            'first_name': customer_info.get('firstname'),
            'last_name': customer_info.get('lastname'),
            'email': customer_info.get('email'),
            'address': {
                'street': customer_info.get('street'),
                'city': customer_info.get('city'),
                'country': customer_info.get('country'),
                'zip_code': customer_info.get('zip')
            },
            'phone': customer_info.get('phone')
        }

        event_notification = event.notification_event(required_action='customer-sign-up', payload=payload)

        response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])
        if response['message'] == 'succeed':
            if response['payload']['customer_sign_up'] == 'Signed Up Successfully':
                return render_template('customer_signin_after_signup_page.html', year=datetime.datetime.now().year)
            else:
                # TODO
                # Add template page
                # TODO
                return response
        elif response['message'] == 'failed':
            return response['payload']
    elif request.method == "GET":
        return render_template('customer_signup.html', year=datetime.datetime.now().year)
