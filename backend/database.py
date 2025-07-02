import os
import psycopg2
import logging
from typing import List
from contextlib import contextmanager


def get_db_connection():
    """Get database connection parameters from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'parliament_attendance'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'port': os.getenv('DB_PORT', '5432')
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
        cursor.execute("""
            INSERT INTO minutes (ref, date, session, url, is_temporary,
                               text_integral)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (ref) DO UPDATE SET
                date = EXCLUDED.date,
                session = EXCLUDED.session,
                url = EXCLUDED.url,
                is_temporary = EXCLUDED.is_temporary,
                text_integral = EXCLUDED.text_integral
        """, (
            minute.ref,
            minute.date,
            minute.session,
            minute.url,
            minute.is_temporary,
            minute.text_integral
        ))
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
                minute.text_integral
            )
            for minute in minutes
        ]
        
        cursor.executemany("""
            INSERT INTO minutes (ref, date, session, url, is_temporary,
                               text_integral)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (ref) DO UPDATE SET
                date = EXCLUDED.date,
                session = EXCLUDED.session,
                url = EXCLUDED.url,
                is_temporary = EXCLUDED.is_temporary,
                text_integral = EXCLUDED.text_integral
        """, data)
        
        logging.info(f"Inserted/Updated {len(minutes)} minutes in database")


def check_database_connection():
    """Test database connection."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()  # Just test the connection
            logging.info("Database connection successful")
            return True
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False
