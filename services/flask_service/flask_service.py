#!/usr/bin/python
import os

from flask_app import create_app

mediator_application = create_app(os.path.join(os.path.dirname(__file__), 'config', 'config_file.ini'),
                                  os.environ['RABBITMQ_CONF'])


if __name__ == '__main__':
    mediator_application.run(debug=True,
                             host=mediator_application.config['FLASK_IP_ADDR'],
                             port=mediator_application.config['FLASK_PORT_NUMBER'])
