FROM python:3.8-alpine

RUN python -m pip install --upgrade pip

RUN adduser -D temp_user
USER temp_user

WORKDIR /home/temp_user

ENV PATH="/home/temp_user/.local/bin:${PATH}"

COPY --chown=temp_user:temp_user ./services/logging_service/ .
COPY --chown=temp_user:temp_user ./config/ ./config/
COPY --chown=temp_user:temp_user ./rabbitMQ_broker/exchange ./exchange/

RUN pip install --user -r requirements.txt

CMD [ "python", "-u", "logging_service.py" ]
