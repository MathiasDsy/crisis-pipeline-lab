import os

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    return psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor,
    )

def check_database_connection() -> dict:
    try:
        conn = get_connection()

        with conn.cursor() as cur:
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()

        conn.close()

        return {
            "connected": True,
            "result": result,
        }

    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }