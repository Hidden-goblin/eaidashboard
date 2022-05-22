FROM python:3.9-alpine

WORKDIR /usr/src/dashboard

RUN pip install pipenv

COPY Pipfile .
COPY main.py .
COPY app app/

RUN pipenv install

CMD pipenv run python main.py