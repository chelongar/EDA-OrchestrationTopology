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

        # Validate the required fields
        missing_fields = validate_customer_info(customer_info)
        if missing_fields:
            print(f"Missing fields: {', '.join(missing_fields)}")
            return jsonify({'error': 'Incomplete registration information'}), 400

        payload = construct_payload(customer_info)

        # Send event notification and handle response
        event_notification = event.notification_event(required_action='customer-sign-up', payload=payload)
        response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])

        # Handle the response from the customer service
        return handle_response(response)

    return render_template('customer_signup.html', year=datetime.datetime.now().year)


def validate_customer_info(customer_info):
    """Validate required customer info fields."""
    required_fields = ['email', 'firstname', 'lastname', 'street', 'password', 'username']
    missing_fields = [field for field in required_fields if not customer_info.get(field)]
    return missing_fields


def construct_payload(customer_info):
    """Construct payload for the customer sign-up."""
    return {'username': customer_info.get('username'),
            'password': customer_info.get('password'),
            'first_name': customer_info.get('firstname'),
            'last_name': customer_info.get('lastname'),
            'email': customer_info.get('email'),
            'address': {'street': customer_info.get('street'),
                        'city': customer_info.get('city', ''),
                        'country': customer_info.get('country', ''),
                        'zip_code': customer_info.get('zip', '')},
            'phone': customer_info.get('phone', '')}


def handle_response(response):
    """Handle the response from the service."""
    if response['message'] == 'succeed':
        if response['payload'].get('customer_sign_up') == 'Signed Up Successfully':
            return render_template('customer_signin_after_signup_page.html', year=datetime.datetime.now().year)
        else:
            # TODO: Add a proper template or response for this case
            return jsonify({'error': 'Unexpected response during sign-up'}), 500
    elif response['message'] == 'failed':
        return jsonify(response['payload']), 400
    else:
        return jsonify({'error': 'Unexpected response format'}), 500