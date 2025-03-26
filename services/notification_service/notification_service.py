import json
import configparser
import smtplib
import os
from collections import defaultdict
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List

import pika
from invoice_generator_pdf import invoice_generator_pdf
from exchange import receiver_exchange


class EmailNotificationSender:
    def __init__(self, sender_email: str, sender_password: str):
        if not sender_email or not isinstance(sender_email, str):
            raise ValueError("Sender email must be a non-empty string.")
        if not sender_password or not isinstance(sender_password, str):
            raise ValueError("Sender password must be a non-empty string.")

        self.sender_email = sender_email
        self.sender_password = sender_password

    def __call__(self, payload: dict, required_action: str, invoice_path: str = '') -> None:
        message = MIMEMultipart()
        message['From'] = self.sender_email
        message['To'] = payload['email']
        message['Subject'] = payload['subject']

        html_content, styles = self._load_template(required_action)
        html_with_css = f"<style>{styles}</style>{html_content.format(**self._get_template_vars(payload, required_action))}"
        message.attach(MIMEText(html_with_css, 'html', 'utf-8'))

        if required_action == 'email-invoice':
            invoice_generator_pdf(f"{payload['first_name']} {payload['last_name']}",
                                  payload['email'],
                                  payload['purchased_items'],
                                  payload['total_price'],
                                  invoice_path)

            with open(invoice_path, "rb") as pdf_file:
                pdf_attachment = MIMEApplication(pdf_file.read(), _subtype="pdf")
                pdf_attachment.add_header('Content-Disposition', 'attachment', filename=invoice_path)
                message.attach(pdf_attachment)

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, message['To'], message.as_string())
        except Exception as e:
            print(f"Failed to send email: {e}")

        if __debug__:
            print("Email sent successfully.")

    def _load_template(self, action: str) -> (str, str):
        try:
            if action == 'email-signup':
                html = open('templates/email_signup_template.html').read()
                css = open('static/email_signup_style.css').read()
            elif action == 'email-invoice':
                html = open('templates/invoice_email_template.html').read()
                css = open('static/invoice_email_style.css').read()
            else:
                raise ValueError(f"Unsupported email action: {action}")
            return html, css
        except Exception as e:
            raise RuntimeError(f"Failed to load email template or style: {e}")

    def _get_template_vars(self, payload: dict, action: str) -> dict:
        base_vars = {
            'first_name': payload['first_name'],
            'last_name': payload['last_name'],
            'title': 'Wonderland Bookstore'
        }
        if action == 'email-invoice':
            unique_items = defaultdict(lambda: {'Item': '', 'Quantity': 0, 'Price': 0})
            for item in payload['purchased_items']:
                key = (item['Title'], item['Price'])
                unique_items[key]['Item'] = item['Title']
                unique_items[key]['Quantity'] += 1
                unique_items[key]['Price'] = item['Price']
            invoice_items = ''.join(
                f"<tr><td>{data['Item']}</td><td>{data['Quantity']}</td><td>${data['Price']}</td></tr>"
                for data in unique_items.values()
            )
            base_vars['invoice_items'] = invoice_items
            base_vars['total_amount'] = payload['total_price']
        return base_vars


class NotificationHandler(receiver_exchange.receiver_exchange):
    def __init__(self, rabbitmq_params, binding_keys: List[str], exchange_name: str,
                 exchange_type: str, email_address: str, email_password: str):
        super().__init__(rabbitmq_params, binding_keys, exchange_type, exchange_name)
        self.email_sender = EmailNotificationSender(email_address, email_password)

    def message_body_analyzer(self, **kwargs):
        message_body_raw = kwargs.get('message_body', b'').decode('utf-8')
        try:
            message_body = json.loads(message_body_raw)
        except json.JSONDecodeError:
            print("Invalid message format.")
            return

        if __debug__:
            print(json.dumps(message_body, indent=2))

        self.email_sender(payload=message_body['payload'],
                          required_action=message_body['required_action'],
                          invoice_path='invoice.pdf')

        return message_body.get('message')


def notification_handler_main():
    try:
        config = configparser.ConfigParser()
        config.read(os.environ['RABBITMQ_CONF'])
        email_address = os.environ['NOTIFICATION_EMAIL_ADDRESS']
        email_password = os.environ['NOTIFICATION_EMAIL_PASSWORD']
        rabbitmq_params = pika.URLParameters(os.environ['RABBITMQ_URL'])

        _NotificationHandler = NotificationHandler(rabbitmq_params,
                                                   ['notification.*'],
                                                   config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_NAME'],
                                                   config['RABBITMQ_BROKER']['NOTIFICATION_EXCHANGE_TYPE'],
                                                   email_address, email_password)
        _NotificationHandler()

    except Exception as e:
        print(f"Failed to start NotificationHandler: {e}")


if __name__ == '__main__':
    notification_handler_main()
