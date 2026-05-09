# Plain SQL to SQLAlchemy Core Migration

## Summary

This document describes the migration pattern used to replace plain SQL strings with SQLAlchemy Core statements in the `pg_projects` database module.

The goal is to make PostgreSQL query code easier to compose, inspect, type, and reuse while keeping the existing psycopg connection pool and execution model.

## Target Structure

Project-related PostgreSQL modules must be grouped under a dedicated `projects` folder:

```text
app/database/postgre/projects/
├── __init__.py
├── pg_projects.py
└── projects_query.py
```

The responsibilities are split as follows:

- `pg_projects.py`: public database functions, validation, connection handling, row mapping, exception mapping.
- `projects_query.py`: SQLAlchemy Core query builders only.

This mirrors the existing pattern used by other grouped PostgreSQL modules, such as `app/database/postgre/bugs`.

## Naming Convention

Query builder functions must:

- live outside the `pg_*.py` module;
- start with `build_`;
- describe the query they create;
- return SQLAlchemy Core statements such as `Select` or `Insert`.

Examples:

```python
def build_registered_projects_query() -> Select:
    return select(projects.c.name)


def build_create_project_version_query(project_name: str, version: str) -> Insert:
    project_id_query = select(projects.c.id, literal(version)).where(projects.c.alias == project_name)
    return insert(versions).from_select(["project_id", "version"], project_id_query).returning(versions.c.id)
```

Avoid names such as `query_projects`, `get_projects_sql`, or private helper query names that do not start with `build_`.

## Migration Steps

1. Create a domain folder under `app/database/postgre`.

For `pg_projects`, the new folder is:

```text
app/database/postgre/projects
```

2. Move the public database module into the domain folder.

The old module:

```text
app/database/postgre/pg_projects.py
```

becomes:

```text
app/database/postgre/projects/pg_projects.py
```

3. Add a separate query module.

For projects:

```text
app/database/postgre/projects/projects_query.py
```

4. Replace inline SQL strings with SQLAlchemy Core builders.

Before:

```python
connection.execute(
    "select name from projects;"
)
```

After:

```python
query, params = _compile(build_registered_projects_query())
connection.execute(query, params)
```

5. Update all imports.

Before:

```python
from app.database.postgre.pg_projects import registered_projects
```

After:

```python
from app.database.postgre.projects.pg_projects import registered_projects
```

## Building Queries

Use table definitions from `app.database.models.metadata` instead of writing table and column names by hand:

```python
from app.database.models.metadata import projects, versions
```

Use SQLAlchemy Core constructs for each SQL operation:

- `select(...)` for `SELECT`
- `insert(...)` for `INSERT`
- `func.count(...)` for aggregates
- `.where(...)` for predicates
- `.join(...)` for joins
- `.limit(...)` and `.offset(...)` for pagination
- `.returning(...)` for inserted or updated identifiers
- `.scalar_subquery()` for scalar nested selects

The `get_projects` query was migrated from string-based subqueries to SQLAlchemy Core aliases and scalar subqueries:

```python
future_versions = versions.alias("future_versions")

future_count = (
    select(func.count(future_versions.c.id))
    .where(future_versions.c.project_id == projects.c.id)
    .where(future_versions.c.status == "recorded")
    .scalar_subquery()
)

query = select(
    projects.c.name.label("name"),
    func.coalesce(future_count, 0).label("future"),
)
```

Column labels must match the keys expected by the existing Pydantic schemas and row consumers.

## Executing Queries

The project still executes SQL through psycopg. SQLAlchemy is used to build and compile SQL, not to manage sessions.

Compile statements with the PostgreSQL dialect before execution:

```python
from sqlalchemy.dialects import postgresql


def _compile(query: Any) -> tuple[str, dict]:
    compiled = query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True})
    return compiled.string, compiled.params
```

Then execute with the current connection:

```python
query, params = _compile(build_get_projects_query(skip=skip, limit=limit))

with pool.connection() as connection:
    connection.row_factory = dict_row
    rows = connection.execute(query, params)
```

This keeps the existing pool, row factories, transactions, and exception handling intact.

## Parameter Handling

Do not interpolate values into SQL strings. Pass values into SQLAlchemy expressions:

```python
select(projects.c.id).where(projects.c.alias == project_name)
```

SQLAlchemy compiles those values into bind parameters consumed by psycopg:

```python
connection.execute(compiled.string, compiled.params)
```

This preserves parameter binding and avoids SQL injection risks.

## Error Handling

Keep database exception handling in the `pg_*.py` module, not in the query builder module.

Example:

```python
try:
    query, params = _compile(build_create_project_version_query(provide(project_name), project.version))
    with pool.connection() as connection:
        connection.row_factory = dict_row
        row = connection.execute(query, params).fetchone()
except IntegrityError as ie:
    result = ApplicationError(...)
```

Query builders should not know about `ApplicationError`, Pydantic schemas, row factories, or API behavior.

## Verification Checklist

For each migrated module:

- Plain SQL strings are removed from the domain `pg_*.py` module.
- Query builders live in a separate module.
- Query builder names start with `build_`.
- Query builders use metadata table objects instead of hard-coded table names.
- Public imports are updated to the new domain folder.
- Row labels still match schema fields.
- Pagination, ordering, and filtering behavior are preserved.
- Inserts still return the expected identifier when callers depend on it.
- Database exceptions are still mapped in the public database module.
- New query builders compile with the PostgreSQL dialect.

Useful verification commands:

```bash
python3 -m py_compile app/database/postgre/projects/pg_projects.py app/database/postgre/projects/projects_query.py
poetry run python -c "from sqlalchemy.dialects import postgresql; from app.database.postgre.projects.projects_query import build_get_projects_query; build_get_projects_query(0, 10).compile(dialect=postgresql.dialect(), compile_kwargs={'render_postcompile': True}); print('ok')"
```

## Notes From `pg_projects`

The migration intentionally did not change the database access technology. The code still uses `app.utils.pgdb.pool` and psycopg connections.

The migration changed where SQL is expressed:

- before: inline SQL strings inside `pg_projects.py`;
- after: SQLAlchemy Core statements in `projects_query.py`, compiled and executed by `pg_projects.py`.

This provides a path to migrate other PostgreSQL modules incrementally without requiring a full ORM or session-based rewrite.
