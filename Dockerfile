FROM python:latest

ENV PYTHONPATH=.

RUN apt-get update && apt-get install -y ghostscript

RUN mkdir -p /code
COPY . /code
WORKDIR /code

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
