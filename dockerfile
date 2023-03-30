FROM python:3.11.0-slim-buster AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential
RUN pip install pipenv

COPY Pipfile ./
RUN pipenv install
RUN pipenv requirements > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN rm -f ./app/static/*

# Stage 2 - Build final image
FROM python:3.11.0-slim-buster

WORKDIR /usr/src/dashboard

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

COPY main.py ./

COPY --from=builder /app/app app/

CMD ["python", "main.py"]