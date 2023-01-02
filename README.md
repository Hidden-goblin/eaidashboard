# EAIDASHBOARD

Simple test campaign dashboard using FastApi, Jinja2 and Mongo db. 

Docker image accessible on [dockerhub](https://hub.docker.com/r/hiddengob/eaidashboard)

## Access dashboard

`<url>:<port>/`

## Access swagger

`<url>:<port>/docs`

## Environment parameters

```text
MONGO_URL=<the mongo db url>
MONGO_PORT=<the mongo db port>
MONGO_USR=<the mongo db username>
MONGO_PWD=<the mongo db user's password>
TIMEDELTA=<time in minutes before token validity expiration>
PG_URL=<the postgres db url>
PG_PORT=<the postgres db port>
PG_USR=<the postgres db user>
PG_PWD=<the postgres db user password>
PG_DB=<the postgres db name>
```

## First start app

By default, an admin is created. Its name is `admin@admin.fr` and its password is `admin`. Please mind updating its password :)

http://localhost:8081/openapi.json

# Version history

## Current: 1.5

## History

- 1.5
  - Add front bug management
  - Remove rsa key dependency
  - Add rsa key automatic generation and renewal
- 1.4
  - Add test repository management
- 1.2
  - Add JWT generation using asymmetric key
- 1.1
  - Fix API issues
  - Move MongoDb collection naming from string to enum
- 1.0
  - First API release