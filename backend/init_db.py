import os
import psycopg2

DB_NAME = os.getenv('DB_NAME', 'parliament_attendance')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')


def create_database():
    conn = psycopg2.connect(
        dbname='postgres',
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cur.fetchone()
    if not exists:
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"✅ Base {DB_NAME} créée")
    else:
        print(f"ℹ️  Base {DB_NAME} existe déjà")
    cur.close()
    conn.close()


def run_schema():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    with open(SCHEMA_PATH, 'r') as f:
        cur.execute(f.read())
    conn.commit()
    print("✅ Schéma exécuté")
    cur.close()
    conn.close()


if __name__ == "__main__":
    create_database()
    run_schema()
