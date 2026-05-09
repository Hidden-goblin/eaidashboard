# EAIDashboard

FastAPI, Python 3.14, PostgreSQL, Redis, SQLAlchemy 2.0, Alembic, Psycopg2, poetry, VUE.

## Commands

- `python3 main.py --dev-https`: Dev server (port 8000)
- `coverage run`: Full python test suite
- `ruff format`: Code format
- `ruff check --fix`: Lint
- `alembic upgrade head`: Migrations
- `./test-frontend`: Frontend VITE test suite
- `./build-frontend`: Build the frontend


## Architecture

- /app/database         Business logic
- /app/database/models  SQLAlchemy models
- /app/database/postgre PostgreSQL business logic
- /app/database/redis   Redis temporary data logic
- /app/documentation/   User manual
- /app/routers/rest     REST API routes definition
- /app/routers/front    Obsolete front routes
- /app/schema           Pydantic v2 schemas definition
- /frontend             VUE frontend

## Rules

- Type hints on all functions.
- No unused import, function attribute, variable
- List ends by a comma
- Always use f-string for string building
- Handlers delegate to services. No business logic in routes.
- Never modify /app/front Sync code, intentionally.
- Never commit .env file
- VUE frontend use the compose API