# Stage 1 - Install dependencies

FROM python:3.11.0-slim-buster AS builder-dep

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential
RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-directory
RUN poetry export -f requirements.txt --output requirements.txt

FROM python:3.11.0-slim-buster AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

COPY --from=builder-dep /app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Cleaning folders from dev elements
COPY app ./app
RUN rm -f ./app/static/*
RUN rm -f ./app/assets/documentation/*

# Stage 2 - Convert PlantUML diagrams to SVG
FROM openjdk:8-jre-slim AS plantuml-builder

RUN apt-get update && apt-get install -y graphviz wget

WORKDIR /app

RUN wget https://sourceforge.net/projects/plantuml/files/plantuml.jar/download -O plantuml.jar

COPY documentation/doc_diag/*.puml ./diagrams/
RUN java -jar plantuml.jar -tsvg diagrams/*.puml


# Stage 3 - Build final image
FROM python:3.11.0-slim-buster

WORKDIR /usr/src/dashboard

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

COPY main.py ./

COPY --from=builder /app/app app/
COPY --from=plantuml-builder /app/diagrams app/assets/documentation

CMD ["python", "main.py"]