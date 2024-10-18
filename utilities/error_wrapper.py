import json
import traceback
import datetime

class error_wrapper:
    def __init__(self, exception):
        self.exception = exception
        self.error_info = self.__exception_details()
    
    def __exception_details(self):
        return {
            "time": datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S"),
            "type": type(self.exception).__name__,
            "message": str(self.exception),
            "traceback": traceback.format_exc()
        }
    
    def to_json(self):
        return self.error_info
