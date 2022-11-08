FROM python:3.9-slim-buster
USER root

RUN apt-get update  \
    && apt-get install -y graphviz \
    && apt-get install -y tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV TZ Asia/Tokyo

RUN mkdir -p /root/src \
    && mkdir -p /root/resources \
    && mkdir -p /root/output

WORKDIR /root

RUN python3 -m pip install --upgrade pip  \
    && pip install graphviz sql-metadata

