#!/usr/bin/env python
import ast
import configparser
import json
import smtplib
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from invoice_generator_pdf import invoice_generator_pdf
import pika
from email.mime.text import MIMEText
from exchange import receiver_exchange


class email_notification_sender:
    def __init__(self, email_sender_addr: str, email_sender_password: str):
        self.email_sender_addr = email_sender_addr
        self.email_sender_password = email_sender_password

    def __call__(self, payload, required_action, invoice_path=''):
        # Read the HTML file
        if required_action == 'email-signup' or required_action == 'email-invoice':
            with open('templates/email_signup_template.html', 'r') as file:
                html_content = file.read()

            with open('static/email_signup_style.css', 'r') as file:
                email_style = file.read()
        else:
            pass

        template_vars = {
            'first_name': payload['first_name'],
            'last_name': payload['last_name'],
            'title': 'Wonderland Bookstore',
            'styles': email_style
        }

        # Replace placeholders with actual values
        html_content = html_content.format(**template_vars)
        _message = MIMEMultipart()
        _message['From'] = self.email_sender_addr
        _message['To'] = payload['email']
        _message['Subject'] = payload['subject']

        # Combine HTML and CSS by embedding CSS within the HTML
        html_with_css = f"<style>{email_style}</style>{html_content}"

        # Attach the HTML content (with CSS) to the email
        _message.attach(MIMEText(html_with_css, 'html', 'utf-8'))

        if required_action == 'email-invoice':
            # Call Invoice Generator
            invoice_generator_pdf(payload['first_name'] + ' ' + payload['last_name'],
                                  payload['email'], payload['purchased_items'], payload['total_price'], invoice_path)

            with open(invoice_path, "rb") as pdf_file:
                pdf_attachment = MIMEApplication(pdf_file.read(), _subtype="pdf")
                pdf_attachment.add_header('Content-Disposition', 'attachment', filename=invoice_path)
                _message.attach(pdf_attachment)

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as SMTP_server:
                SMTP_server.login(_message['From'], self.email_sender_password)
                SMTP_server.sendmail(_message['From'], _message['To'], _message.as_string())
        except Exception as e:
            print(f"Failed to send email: {e}")

        if __debug__:
            print("Message Sent Successfully!")


class notification_handler(receiver_exchange.receiver_exchange):
    def __init__(self, rabbitmq_params: object, topic_binding_keys: list,
                 notification_exchange_name: str, notification_exchange_type: str,
                 notification_email_addr: str, notification_email_pass: str):
        super().__init__(rabbitmq_params, topic_binding_keys, notification_exchange_type, notification_exchange_name)

        self.notification_email_addr = notification_email_addr
        self.notification_email_pass = notification_email_pass

    @property
    def notification_email_addr(self):
        return self._notification_email_addr

    @notification_email_addr.setter
    def notification_email_addr(self, value):
        if not isinstance(value, str):
            raise ValueError("Sender e-mail address MUST be a string.")
        if not value:
            raise ValueError("Sender e-mail address MUST CAN NOT be empty string.")
        self._notification_email_addr = value

    @property
    def notification_email_pass(self):
        return self._notification_email_pass

    @notification_email_pass.setter
    def notification_email_pass(self, value):
        if not isinstance(value, str):
            raise ValueError("Sender e-mail password MUST be a string.")
        if not value:
            raise ValueError("Sender e-mail password MUST CAN NOT be empty string.")
        self._notification_email_pass = value

    def message_body_analyzer(self, **kwargs):

        for key, value in kwargs.items():
            if key == 'message_body':
                message_body = value

        _message_body = ast.literal_eval(str(json.loads(message_body)))

        if __debug__:
            print(json.dumps(_message_body, sort_keys=True))

        _email_notification_sender = email_notification_sender(self.notification_email_addr,
                                                               self.notification_email_pass)
        _email_notification_sender(_message_body['payload'],
                                   _message_body['required_action'],
                                   invoice_path="invoice.pdf")

        return _message_body.get('message')


def notification_handler_main():
    try:
        rabbitmq_config = configparser.ConfigParser()
        rabbitmq_config.read(os.environ['RABBITMQ_CONF'])
    except KeyError:
        print("--> ERROR: The environment variable is not set.")
    except FileNotFoundError:
        print(f" --> ERROR: The file at {os.environ['RABBITMQ_CONF']} was NOT found.")
    except Exception as err:
        print(f" --> ERROR: {err}")

    try:
        NOTIFICATION_EMAIL_ADDRESS = os.environ['NOTIFICATION_EMAIL_ADDRESS']
    except KeyError:
        print("Environment variable 'NOTIFICATION_EMAIL_ADDRESS' not found.")

    try:
        NOTIFICATION_EMAIL_PASSWORD = os.environ['NOTIFICATION_EMAIL_PASSWORD']
    except KeyError:
        print("Environment variable 'NOTIFICATION_EMAIL_PASSWORD' not found.")

    rabbitmq_params = pika.URLParameters(os.environ['RABBITMQ_URL'])

    _notification_handler = notification_handler(rabbitmq_params,
                                                 ['notification.*'],
                                                 rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_NAME'],
                                                 rabbitmq_config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_TYPE'],
                                                 NOTIFICATION_EMAIL_ADDRESS,
                                                 NOTIFICATION_EMAIL_PASSWORD)
    _notification_handler()


if __name__ == '__main__':
    notification_handler_main()
