# Dashboard documentation

[TOC]

## Foreword

This tool's purpose is to help building and conducting test campaigns. One of the main goal is to provide transparency on the test status.

A second goal is to aggregate tests results on the long term, and display scenarios or features or epics which are prone to failure.

With integration in CI/CD in mind, the tool is API first developed and then GUI because manual testers may use it.

## Installation

The tool is scripted in python. You can clone the github repository and play with it :) However, the tool is 
released as docker image so that you can use it we ease.

The data persistence is powered by Postgresql. Redis helps for transient data.

If you display this page, you've already installed the application. However, if you mean to proceed to another 
installation or help someone to install.

### Cloning (not recommended)

**Please note**: This how to is based on my personal usage. You might know different way to achieve the same purpose 
using another python virtual environment.

First make sure you have python 3.12 installed on your pc. Add the `pipenv` package as you will need to run the 
application within this environment.

Secondly, clone the repository onto your disk. 

```commandline
git clone https://github.com/Hidden-goblin/eaidashboard.git
```

Install a postgresql and redis database. I will let you choose the best way to proceed to the installation as this 
documentation is not about postgresql nor redis.

From within the `eaidashboard` repository.

Create a `.env` file with the following variable correctly filled.

```
PG_URL= your postgresql url here
PG_PORT= your postgresql port here
PG_USR= your postgresql username here
PG_PWD= your postgresql user's password here
PG_DB= your database name for the project
REDIS_URL= your redis url here
REDIS_PORT= your redis port here
TIMEDELTA= token expiration in minutes
SESSION_KEY= your session key
```

Then run

```commandline
pipenv install
pipenv run python main.py
```

You should be able to access the application.

### Docker-compose (recommended)

First make sure you have docker running for your platform.

Then create the docker-compose file with the following content

```dockerfile
services:
  db:
    container_name: dash_postgres
    image: postgres
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: root
      POSTGRES_DB: postgres
    ports:
      -  8082:5432
    networks:
      - dashboard
    volumes:
      - pgdb-data:/var/lib/postgresql/data
  redis:
    container_name: dash_redis
    image: redis:7-alpine
    ports:
      - 8084:6379
    networks:
       - dashboard
  app:
    container_name: dash_application
    image: hiddengob/eaidashboard:3.8
    environment:
      SESSION_KEY: 'averylongsessionkeyyouhavegenerated'  
      TIMEDELTA: 10
      PG_USR: root
      PG_PWD: root
      PG_URL: db
      PG_PORT: 5432
      PG_DB: testdash
      REDIS_URL: redis
      REDIS_PORT: 6379
    ports:
      - 8081:8081
    networks:
      - dashboard

networks:
  dashboard:

volumes:
  pgdb-data:
```

Then eventually run the docker compose command to start the application. It should be something like

```commandline
docker-compose -p testdashboard up -d
```

Make sure, your user have the right to run docker command.

## Links

The application GUI should be accessible at [root url](/)

The application API documentation is accessible at [swagger page](/docs)

The application source code repository is accessible on [github](https://github.com/Hidden-goblin/eaidashboard).

The docker-hub link for [app image](https://hub.docker.com/r/hiddengob/eaidashboard).

## <img height="10" src="/assets/camera.svg" width="10"/> Topics

<a class="link-primary" hx-get="/documentation/00-workflows.md">Designed workflows</a>

<a class="link-primary" hx-get="/documentation/00-how_to.md">How-to page</a>

<a class="link-primary" hx-get="/documentation/00-br_rights.md">Roles and permissions</a>




