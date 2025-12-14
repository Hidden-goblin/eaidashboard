
from app.utils.pgdb import get_connection


def test_get_connection(application):
    """Test the get_connection function."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1
