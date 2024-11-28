from configparser import ConfigParser

from current_customer import current_customer
from flask import Flask
from flask_login import LoginManager

login_manager = LoginManager()


def load_config(config_file, section, required_keys) -> dict:
    """
    Load configuration from a file and section, ensuring that all required keys are present.

    :param config_file:     Path to the config file.
    :param section:         Section in the config file to load.
    :param required_keys:   List of required keys within the section.
    :return:                Dictionary of loaded configuration values.
    :raises:                KeyError, FileNotFoundError, or Exception for missing keys or file errors.
    """
    config = ConfigParser()
    try:
        config.read(config_file)
        return {key: config[section][key] for key in required_keys}
    except KeyError as e:
        print(f"--> ERROR: Missing key {e} in section '{section}' of {config_file}.")
        raise
    except FileNotFoundError:
        print(f"--> ERROR: The file at {config_file} was NOT found.")
        raise
    except Exception as err:
        print(f"--> ERROR: An error occurred while reading {config_file}: {err}")
        raise


def create_app(flask_config_filename=None, rabbitmq_config_file=None):
    app = Flask(__name__)

    try:
        flask_keys = ['IP_ADDR', 'PORT_NUMBER']
        flask_config = load_config(flask_config_filename, 'FLASK_INFO', flask_keys)
        app.config.update({'FLASK_IP_ADDR': flask_config['IP_ADDR'],
                           'FLASK_PORT_NUMBER': flask_config['PORT_NUMBER']})
    except Exception:
        print("--> ERROR: Failed to load Flask configuration.")

    try:
        rabbitmq_keys = ['PAYMENT_QUEUE', 'INVENTORY_QUEUE', 'LOGGING_EXCHANGE_TYPE', 'LOGGING_EXCHANGE_NAME',
                         'CUSTOMER_SERVICE_QUEUE', 'NOTIFICATION_EXCHANGE_TYPE', 'NOTIFICATION_EXCHANGE_NAME']
        rabbitmq_config = load_config(rabbitmq_config_file, 'RABBITMQ_BROKER', rabbitmq_keys)
        app.config.update(rabbitmq_config)
    except Exception:
        print("--> ERROR: Failed to load RabbitMQ configuration.")

    # Set secret key
    app.secret_key = 'MY_SECRET_KEY'

    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.customer_sign_in'

    from .main.routes import main_blueprint
    from .auth.routes import auth_blueprint
    from .signup.routes import signup_blueprint
    from .payment.routes import payment_blueprint
    from .customer_basket.routes import basket_blueprint

    blueprints = [(main_blueprint, '/'),
                  (auth_blueprint, '/auth'),
                  (signup_blueprint, '/'),
                  (basket_blueprint, '/basket'),
                  (payment_blueprint, '/')]

    for blueprint, prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=prefix)

    return app

@login_manager.user_loader
def load_user(_id):
    return current_customer.get_from_customer_service(_id)
