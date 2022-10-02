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
ALGORITHM="RS256"
DASH_PRIVATE=<path to private ssh key. Should not be accessible from network>
DASH_PUBLIC=<path to public ssh key. May be accessible from network>
PG_URL=<the postgres db url>
PG_PORT=<the postgres db port>
PG_USR=<the postgres db user>
PG_PWD=<the postgres db user password>
PG_DB=<the postgres db name>
```

## First start app

By default, an admin is created. Its name is `admin@admin.fr` and its password is `admin`. Please mind updating its password :)

http://localhost:8081/openapi.json