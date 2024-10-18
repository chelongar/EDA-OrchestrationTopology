import json
import os
import datetime
import uuid


class event:
    def __init__(self):
        self.source_service = os.environ.get('SERVICE_NAME', 'unknown_service')
        self.date_time = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
        self.event_id = str(uuid.uuid4())

    def __call__(self, requested_format='json'):
        if requested_format == 'json':
            return self.__to_json()
        elif requested_format == 'dict':
            return self.__to_dict()
        else:
            raise ValueError("Unsupported requested format")

    def __to_json(self):
        return json.dumps(self.__to_dict())

    def __to_dict(self):
        event_dict = self.__dict__.copy()
        return event_dict


class notification_event(event):
    def __init__(self, required_action: str, payload: dict):
        super().__init__()
        self.required_action = required_action
        self.payload = payload


class log_event(event):
    def __init__(self, log_severity: str):
        super().__init__()
        """

        :type log_severity: str
        """
        self.log_severity = log_severity


class notification__service_message(event):
    def __init__(self, email_necessity: bool):
        """

        :type email_necessity: bool
        """
        super().__init__()
        self.email_necessity = email_necessity


class domain_event(event):
    def __init__(self, correlation_id: str, payload: dict):
        """

        :param correlation_id:  Domain Event Correlation ID
        :param payload:         Domain Event Payload
        """
        super().__init__()
        self.correlation_id = correlation_id
        self.payload = payload
        self.event_type = 'domain_event'
