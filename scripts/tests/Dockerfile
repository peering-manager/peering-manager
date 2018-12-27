FROM python:3.7-alpine

# avoid docker buffering output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /peering-manager

RUN pip install --upgrade pip
COPY ../.. /peering-manager
RUN pip install -r requirements.txt
