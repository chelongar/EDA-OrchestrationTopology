import datetime
import json
import os

from current_customer import current_customer
from flask import Blueprint, redirect, url_for, request, render_template, current_app
from flask_login import login_user, login_required, logout_user
from utils.helpers import send_message_to_service, logging_message_sender

from utils.helpers import logout_required
from utilities import event

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/customer_sign_in', methods=['GET', 'POST'])
@logout_required
def customer_sign_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        event_notification = event.NotificationEvent(required_action='customer-sign-in',
                                                     payload={'username': username,
                                                               'password': password})
        if os.environ['DEBUG_FLAG'] == 'True':
            logging_message_sender(log_severity='info', payload=event_notification('json'),
                                   exchange_type='direct',
                                   exchange_name='logging_exchange',
                                   message=json.loads(event_notification('json'))['required_action'])

        response = send_message_to_service(event_notification('json'), current_app.config['CUSTOMER_SERVICE_QUEUE'])
        if response['message'] == 'succeed':
            if response['payload']['customer_sign_in'] == 'Login Was Successful':
                _current_customer = current_customer(response.get('payload')['payload']['customer_id'],
                                                     response.get('payload')['payload']['username'])
                login_user(_current_customer)
                return redirect(url_for("main.welcome_page"))
            else:
                return render_template('customer_signin_after_failure.html', year=datetime.datetime.now().year)
        elif response['message'] == 'failed':
            return response['payload']
    elif request.method == "GET":
        return render_template('signin_page.html', year=datetime.datetime.now().year)


@auth_blueprint.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return render_template('signin_page.html', year=datetime.datetime.now().year)


