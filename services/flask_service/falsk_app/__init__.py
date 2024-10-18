import os

from flask import Flask
from configparser import ConfigParser
from flask_login import LoginManager

from current_customer import current_customer

login_manager = LoginManager()


def create_app(flask_config_filename=None, rabbitmq_config_file=None):
    app = Flask(__name__)

    try:
        flask_config = ConfigParser()
        flask_config.read(flask_config_filename)

        app.config['FLASK_IP_ADDR'] = flask_config['FLASK_INFO']['IP_ADDR']
        app.config['FLASK_PORT_NUMBER'] = flask_config['FLASK_INFO']['PORT_NUMBER']
    except KeyError:
        print("--> ERROR: The environment variable is not set.")
    except FileNotFoundError:
        print(f" --> ERROR: The file at {flask_config_filename} was NOT found.")
    except Exception as err:
        print(f" --> ERROR: {err}")

    try:
        rabbitmq_config = ConfigParser()
        rabbitmq_config.read(rabbitmq_config_file)

        app.config['PAYMENT_QUEUE'] = rabbitmq_config['RABBITMQ_BROKER']['PAYMENT_QUEUE']
        app.config['INVENTORY_QUEUE'] = rabbitmq_config['RABBITMQ_BROKER']['INVENTORY_QUEUE']
        app.config['LOGGING_EXCHANGE_TYPE'] = rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_TYPE']
        app.config['LOGGING_EXCHANGE_NAME'] = rabbitmq_config['RABBITMQ_BROKER']['LOGGING_EXCHANGE_NAME']
        app.config['CUSTOMER_SERVICE_QUEUE'] = rabbitmq_config['RABBITMQ_BROKER']['CUSTOMER_SERVICE_QUEUE']
        app.config['NOTIFICATION_EXCHANGE_TYPE'] = rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_TYPE']
        app.config['NOTIFICATION_EXCHANGE_NAME'] = rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_NAME']
    except KeyError:
        print("--> ERROR: The environment variable is not set.")
    except FileNotFoundError:
        print(f" --> ERROR: The file at {rabbitmq_config_file} was NOT found.")
    except Exception as err:
        print(f" --> ERROR: {err}")

    app.secret_key = 'MY_SECRET_KEY'

    login_manager.init_app(app)
    login_manager.login_view = 'auth.customer_sign_in'

    from .main.routes import main_blueprint
    from .auth.routes import auth_blueprint
    from .signup.routes import signup_blueprint
    from .payment.routes import payment_blueprint
    from .customer_basket.routes import basket_blueprint

    app.register_blueprint(main_blueprint, url_prefix='/')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(signup_blueprint, url_prefix='/')
    app.register_blueprint(basket_blueprint, url_prefix='/basket')
    app.register_blueprint(payment_blueprint, url_prefix='/')

    return app


@login_manager.user_loader
def load_user(_id):
    return current_customer.get_from_customer_service(_id)
