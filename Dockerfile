FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD requirements.txt /code/
ADD requirements_dev.txt /code/

RUN pip install -r requirements_dev.txt

ADD . /code

RUN pip install -e .
