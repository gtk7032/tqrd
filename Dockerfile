FROM python:3.9-slim-buster
USER root

RUN apt-get update ; apt-get install -y graphviz
COPY ./src /root
RUN mkdir -p /root/resources
WORKDIR /root

RUN python3 -m pip install --upgrade pip  \
    && pip install graphviz sql-metadata

