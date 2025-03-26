import json
import os
import datetime
import uuid


class Event:
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


class NotificationEvent(Event):
    def __init__(self, required_action: str, payload: dict):
        super().__init__()
        self.required_action = required_action
        self.payload = payload


class LogEvent(Event):
    def __init__(self, log_severity: str):
        super().__init__()
        """

        :type log_severity: str
        """
        self.log_severity = log_severity
