
from psycopg import Connection


def populate_db(conn: Connection):
    """Populate the database with the required data."""
    with conn.cursor() as cur:
        with open("app/sql/db.sql", "r") as f:
            cur.execute(f.read())
    conn.commit()
