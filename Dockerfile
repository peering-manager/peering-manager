FROM python:3
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -qy install postgresql-client
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
COPY docker/entrypoint.sh /code
COPY docker/configuration.py /code/peering_manager
RUN chmod +x /code/entrypoint.sh
