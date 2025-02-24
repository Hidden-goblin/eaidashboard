# EAIDASHBOARD

Simple test campaign dashboard using FastApi, Jinja2 and redis and Postgresql database. 

Docker image accessible on [dockerhub](https://hub.docker.com/r/hiddengob/eaidashboard)

## Access dashboard

`<url>:<port>/`

## Access swagger

`<url>:<port>/docs`

## Environment parameters

```text
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

Use the migration endpoint `GET /api/v1/admin/redis_migration`. The migration process must be launched by an admin.

After the migration is done, restart the application to be sure not to use the mongodb connector. You can even shutdown the mongodb database.

**Please note** version 3.1+ does not provide migration endpoint.

# Version history

## Current: 3.9

## History
- 3.9
  - Add link between bug and test
  - Update to python 3.12
- 3.8
  - Add role management
  - Remap some front routes
  - Fix deliverable not regenerated when bug is updated
  - Introduce some feature documentation (living documentation planned)
  - Upgrade Pydantic to version 2.+
  - Limitation: Project Admin cannot grant rights to user for their project
- 3.7.2
  - Fix BugStatusEnum
  - Fix modal title (bis)
- 3.7.1
  - Fix TER generation: root cause change signature on function retrieving bugs
  - Fix modal title
  - Fix ticket status in TER based on scenarios' status
- 3.7
  - VirtualEnv migration to Poetry
  - Add Bug simple workflow
  - Add ruff static code review
  - Add Front ticket's scenarios statuses count
- 3.6
  - Campaign occurrence status management
  - Update html export
- 3.5
  - Create project (GUI)
  - Update version (GUI)
  - Modal management & events triggering
- 3.4
  - Add some basic documentation and the basics for future documentation.
  - Add plantUml build stage
- 3.3.1
  - Fix issue on deleting keys in redis where keys is an empty list. 
- 3.3
  - Use cache to lower the document generation trigger
  - Remove unnecessary function used with MongoDb
- 3.2.2
  - Fix issue on update version status TypeError strptime argument 1 must be str, not None
- 3.2.1
  - Fix issue on sql request for get_projects. CardinalityError with subquery
- 3.2
  - Fix front closing div
  - Fix missing feature name on ticket-scenario view
  - Fix status wording in campaign-ticket view
  - Add automatic reload in dashboard, campaign ticket, campaign occurrence
  - Add redis file caching for displaying text report
- 3.1
  - Technical version remove mongodb
  - Fix some bugs
  - Fix bson error
- 3.0-1
  - Fix issue where database renaming does not work
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