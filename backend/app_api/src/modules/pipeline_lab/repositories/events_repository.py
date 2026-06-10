import os
import uuid
import psycopg2
import psycopg2.extras


class EventsRepository:
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://crisis:crisis@localhost:5432/crisis_db"
        )

    def _get_connection(self):
        return psycopg2.connect(self.database_url)

    def get_all_events(self):
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT *
                    FROM events
                    ORDER BY updated_at DESC
                """)
                return cur.fetchall()

    def get_event(self, event_id: str):
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT *
                    FROM events
                    WHERE id = %s
                """, (event_id,))
                return cur.fetchone()

    def add_tweet_to_event(
        self,
        event_id: str,
        tweet_id: str,
        tweet_text: str,
    ):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE tweets
                    SET event_id = %s
                    WHERE id = %s
                """, (event_id, tweet_id))

                cur.execute("""
                    UPDATE events
                    SET
                        tweet_count = tweet_count + 1,
                        latest_tweet_text = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (tweet_text, event_id))

                conn.commit()

    def create_event(
        self,
        lat: float,
        lon: float,
        source_text: str,
        tweet_id: str,
        radius_km: float = 20.0,
    ) -> dict:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO events (
                        center_lat,
                        center_lon,
                        radius_km,
                        status,
                        is_finished,
                        tweet_count,
                        latest_tweet_text,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        'active',
                        FALSE,
                        1,
                        %s,
                        NOW(),
                        NOW()
                    )
                    RETURNING
                        id,
                        center_lat,
                        center_lon,
                        radius_km,
                        status,
                        is_finished,
                        tweet_count,
                        latest_tweet_text,
                        created_at,
                        updated_at
                """, (lat, lon, radius_km, source_text))

                event = dict(cur.fetchone())

                cur.execute("""
                    UPDATE tweets
                    SET event_id = %s
                    WHERE id = %s
                """, (event["id"], tweet_id))

                conn.commit()

                return event

        def add_tweet_to_event(self, event_id: str, tweet_id: str):
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE tweets
                        SET event_id = %s
                        WHERE id = %s
                    """, (event_id, tweet_id))

                    conn.commit()

    def create_test_event(self):
        event_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO events (
                        id,
                        center_lat,
                        center_lon,
                        radius_km,
                        status,
                        is_finished,
                        latest_tweet_text,
                        tweet_count
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    event_id,
                    43.5081,
                    16.4402,
                    20.0,
                    "active",
                    False,
                    "Smoke visible over Split harbor",
                    1
                ))
                conn.commit()
                return cur.fetchone()