FROM python:3.11-alpine


RUN apk update &&  pip install pipenv

WORKDIR /usr/src/dashboard

COPY Pipfile main.py ./
COPY app app/

RUN pipenv install && mkdir .ssh/

CMD pipenv run python main.py