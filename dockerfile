FROM python:3.9-alpine


RUN apk update && apk add python3-dev \
                          gcc \
                          libc-dev \
                          libffi-dev

WORKDIR /usr/src/dashboard

RUN pip install pipenv

COPY Pipfile .
COPY main.py .
COPY app app/

RUN pipenv install

RUN mkdir .ssh/

CMD pipenv run python main.py