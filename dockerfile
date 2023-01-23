FROM python:3.11.0-slim

RUN apt-get -y update &&  pip install pipenv

WORKDIR /usr/src/dashboard

COPY Pipfile main.py ./

RUN pipenv install

COPY app app/

CMD pipenv run python main.py