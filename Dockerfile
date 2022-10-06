FROM python:3.9-alpine
USER root

RUN apk --update add graphviz 
COPY ./src /root
RUN mkdir -p /root/resources
WORKDIR /root

RUN python3 -m pip install --upgrade pip  \
    && pip install graphviz sql-metadata

