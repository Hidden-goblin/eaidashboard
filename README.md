# EAIDASHBOARD

Simple test campaign dashboard using FastApi, Jinja2 and redis and Postgresql database. 

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
REDIS_URL=<the redis db url>
REDIS_PORT=<the redis db port>
SESSION_KEY=<the session key>
```

## First start app

By default, an admin is created. Its name is `admin@admin.fr` and its password is `admin`. Please mind updating its password :)

Openapi json description http://localhost:8081/openapi.json
Swagger interface http://localhost:8081/docs

## Migrate from 2.* version to 3.*

You must use the 3.0 version to migrate data from mongodb to postgresql.

Ensure you have set a redis database. 

Use the migration endpoint `GET /api/v1/admin/redis_migration`. The migration process must be launch by an admin.

After the migration is done, restart the application to be sure not to use the mongodb connector. You can even shutdown the mongodb database.


# Version history

## Current: 3.1

## History
- 3.1
  - Technical version remove mongodb
  - Fix some bugs
- 3.0
  - Migrate all mongodb data to postgresql
  - Add Redis for transient data and ttl data
  - Add migration endpoint (Will disappear in next version)
- 2.9
  - Add Test Plan, TER and evidence generation
  - Fix test result import
- 2.8
  - Add capability to register campaign status
  - Add capability to display Map result (scenarios based) for a campaign
- 2.7
  - Avoid creating an existing project. Raise an error doing so.
  - Catch error when the app restart and a user is still connected (SignatureError with new key)
- 2.6.2
  - Fix mongo alias naming for id
  - Fix Object not subscriptable error
- 2.6.1
  - Change the base container
- 2.6
  - Add singleton project name provider
  - Avoid creating database name with `/\. "$*<>:|?` character (alias)
  - Propagate update on mongo queries
  - fix campaign occurrence value when importing all scenarios results
  - fix campaign board previous/next button
- 2.5
  - Add test result post (REST API)
  - Add test result get (REST API)
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