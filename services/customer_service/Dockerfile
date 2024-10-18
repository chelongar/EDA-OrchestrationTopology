FROM python:3.8-alpine

RUN python -m pip install --upgrade pip
RUN apk add --no-cache postgresql-dev gcc musl-dev

RUN adduser -D temp_user
USER temp_user

WORKDIR /home/temp_user

ENV PATH="/home/temp_user/.local/bin:${PATH}"

COPY --chown=temp_user:temp_user ./services/customer_service/ .
COPY --chown=temp_user:temp_user ./config/ ./config/
COPY --chown=temp_user:temp_user ./rabbitMQ_broker/RPC/rpc_server.py ./RPC/rpc_server.py
COPY --chown=temp_user:temp_user ./rabbitMQ_broker/exchange ./exchange/
COPY --chown=temp_user:temp_user ./utilities ./utilities/

RUN pip install --user -r requirements.txt

EXPOSE 5432

CMD [ "python", "-u", "customer_service.py" ]
