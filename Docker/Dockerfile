FROM alpine

RUN apk add --update --virtual --no-cache python3 python3-dev libffi-dev g++ gcc musl-dev openssl-dev py-lxml py-pynacl git \
    && git clone https://github.com/respawner/peering-manager.git \
    && pip3 install --upgrade pip \
    && pip3 install -r peering-manager/requirements.txt

COPY peering_manager/configuration.example.py peering-manager/peering_manager/configuration.py
RUN python3 peering-manager/manage.py migrate && \
    python3 peering-manager/manage.py collectstatic --no-input && \
    python3 peering-manager/manage.py runserver 0.0.0.0:8080 --insecure