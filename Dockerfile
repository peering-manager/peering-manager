FROM ubuntu
MAINTAINER Tim Nowaczyk <zimage@gmail.com>

ADD . /opt/peering-manager

RUN apt update && apt install -y python3 python3-dev python3-pip git vim

RUN cd /opt/peering-manager && \
    pip3 install -r requirements.txt

RUN chmod +x /opt/peering-manager/docker/pmngr
RUN ln -s /opt/peering-manager/docker/pmngr /usr/bin/pmngr

RUN export PATH=$PATH:/usr/bin/

EXPOSE 80
WORKDIR /opt/peering-manager

VOLUME ["/opt/peering-manager/db.sqlite3", "/opt/peering-manager/peering_manager/configuration.py"]

CMD ["/usr/bin/python3", "manage.py", "runserver", "0.0.0.0:80"]
