FROM python:latest

# We copy this file first to leverage docker cache
COPY ./requirements.txt /code/hypernucleusserver/requirements.txt

WORKDIR /code/hypernucleusserver

RUN pip install -r requirements.txt

COPY . /code/hypernucleusserver

RUN python setup.py bdist_wheel
