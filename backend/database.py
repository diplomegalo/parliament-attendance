import os
import psycopg2
import logging
from typing import List
from contextlib import contextmanager


def get_db_connection():
    """Get database connection parameters from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'db'),
        'dbname': os.getenv('DB_NAME', 'parliament_attendance'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', 5432)
    }


@contextmanager
def get_db_cursor():
    """Context manager for database operations."""
    conn = None
    cursor = None
    try:
        conn_params = get_db_connection()
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def insert_minute(minute):
    """Insert a single minute into the database."""
    with get_db_cursor() as cursor:
        # Insertion ou update des métadonnées dans minutes
        cursor.execute("""
            INSERT INTO minutes (ref, date, session, url, is_temporary)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ref) DO UPDATE SET
                date = EXCLUDED.date,
                session = EXCLUDED.session,
                url = EXCLUDED.url,
                is_temporary = EXCLUDED.is_temporary
            RETURNING id
        """, (
            minute.ref,
            minute.date,
            minute.session,
            minute.url,
            minute.is_temporary
        ))
        result = cursor.fetchone()
        if result is None:
            raise Exception("Insertion failed: no id returned")
        minute.id = result[0]

        # Insertion ou update du texte dans minutes_text
        cursor.execute("""
            INSERT INTO minutes_text (minute_id, text_integral)
            VALUES (%s, %s)
            ON CONFLICT (minute_id) DO UPDATE SET
                text_integral = EXCLUDED.text_integral
        """, (minute.id, minute.text_integral))
        logging.debug(f"Inserted/Updated minute {minute.ref}")


def insert_minutes_bulk(minutes: List):
    """Insert multiple minutes into the database."""
    with get_db_cursor() as cursor:
        # Prepare data for bulk insert
        data = [
            (
                minute.ref,
                minute.date,
                minute.session,
                minute.url,
                minute.is_temporary,
            )
            for minute in minutes
        ]

        cursor.executemany("""
            INSERT INTO minutes (ref, date, session, url, is_temporary)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ref) DO UPDATE SET
                date = EXCLUDED.date,
                session = EXCLUDED.session,
                url = EXCLUDED.url,
                is_temporary = EXCLUDED.is_temporary
        """, data)

        text_data = [
            (
                minute.ref,
                minute.text_integral
            )
            for minute in minutes
        ]

        cursor.executemany("""
            INSERT INTO minutes_text (minute_id, text_integral)
            VALUES (
                (SELECT id FROM minutes WHERE ref = %s),
                %s
            )
            ON CONFLICT (minute_id) DO UPDATE SET
                text_integral = EXCLUDED.text_integral
        """, text_data)

        logging.info(f"Inserted/Updated {len(minutes)} minutes in database")


def minute_exists_list(refs: List[str]):
    """Check if a minute exists in the database by its reference."""
    with get_db_cursor() as cursor:
        formated_str = ",".join(["%s"] * len(refs))
        query = f"SELECT ref FROM minutes WHERE ref IN ({formated_str})"
        cursor.execute(query, refs)
        found_ref = {row[0] for row in cursor.fetchall()}
        return all(ref in found_ref for ref in refs)
