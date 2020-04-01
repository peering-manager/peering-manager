## Build Stage
ARG FROM=python:3-alpine
FROM ${FROM} as builder

RUN apk add --no-cache \
      gcc \
      make \
      musl-dev \
      libffi-dev \
      libxml2-dev \
      libxslt-dev \
      libressl-dev \
      postgresql-dev

WORKDIR /install

COPY requirements.txt /
RUN pip install --prefix="/install" --no-cache-dir --no-warn-script-location -r /requirements.txt

## Main Stage
ARG FROM
FROM ${FROM} as main

RUN apk add --no-cache \
      bash \
      libffi \
      libxslt \
      libxml2 \
      libressl \
      postgresql-client

WORKDIR /opt/peering-manager
ENV PYTHONUNBUFFERED 1

COPY --from=builder /install /usr/local
COPY . /opt/peering-manager

RUN apk add --no-cache tzdata && cp /usr/share/zoneinfo/Australia/Brisbane /etc/localtime && echo -n "Australia/Brisbane" > /etc/timezone && apk del --no-cache tzdata
RUN ln -s /opt/peering-manager/docker/ /opt/docker && ln -s /opt/docker/configuration.py /opt/peering-manager/peering_manager/configuration.py && chmod +x /opt/docker/entrypoint.sh