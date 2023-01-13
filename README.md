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
SESSION_KEY=<the session key>
```

## First start app

By default, an admin is created. Its name is `admin@admin.fr` and its password is `admin`. Please mind updating its password :)

http://localhost:8081/openapi.json

# Version history

## Current: 2.4

## History
- 2.4
  - Fix first start async issue on create_user
  - Messages are sent to the footer
    - Add container
    - Remove hyperscript go to url
    - Add htmx retarget and redirect mechanism
  - API add response model to some endpoint (TBC)
- 2.3
  - Fix button & input in html table_bug to include version on patch
- 2.2
  - Fix asyncio behaviour across project
- 2.1 patch 1
  - Fix missing file content
- 2.1
  - Add Front capability to add a ticket to a version
  - Async/await on nearly all methods. Prepare for move ticket from one version to another.
  - Fix bug count update
  - SPEC: Ticket cannot be deleted.
- 2.0
  - Breaking change in database structure
  - Allow to add ticket to campaign without scenarios
- 1.6
  - Fix postgresql connection issue with docker-compose
  - Fix unsecure sql request
  - Add SESSION_KEY parameter
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