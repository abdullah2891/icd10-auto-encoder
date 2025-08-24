# db.py
"""
Centralized PostgreSQL connection logic for ICD10 Auto Encoder
"""
import os
import psycopg2
from pgvector.psycopg2 import register_vector

# Load connection info from environment variables
PG_HOST = os.getenv("PG_HOST")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DBNAME = os.getenv("PG_DBNAME")

def get_pg_conn():
    if PG_HOST and PG_USER and PG_PASSWORD and PG_DBNAME:
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASSWORD,
                dbname=PG_DBNAME
            )
            register_vector(conn)
            print("Connected to PostgreSQL (db.py)")
            return conn
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            return None
    else:
        print("PostgreSQL connection parameters not fully provided.")
        return None
