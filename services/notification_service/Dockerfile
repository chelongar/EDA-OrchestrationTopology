FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" temp_user
USER temp_user

WORKDIR /home/temp_user

ENV PATH="/home/temp_user/.local/bin:${PATH}"

COPY --chown=temp_user:temp_user ./services/notification_service/ .
COPY --chown=temp_user:temp_user ./config/ ./config/
COPY --chown=temp_user:temp_user ./rabbitMQ_broker/exchange ./exchange/

RUN pip install --user -r requirements.txt

CMD [ "python", "-u", "notification_service.py" ]
