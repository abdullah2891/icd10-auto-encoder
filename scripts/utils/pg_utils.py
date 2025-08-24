# utils/pg_utils.py
"""
PostgreSQL utility functions for ICD10 indexer
"""
import psycopg2

def get_pg_connection(args):
    if all([args.pg_host, args.pg_user, args.pg_password, args.pg_dbname]):
        try:
            conn = psycopg2.connect(
                host=args.pg_host,
                port=args.pg_port,
                user=args.pg_user,
                password=args.pg_password,
                dbname=args.pg_dbname
            )
            print("Connected to PostgreSQL.")
            return conn
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            return None
    else:
        print("PostgreSQL connection parameters not fully provided. Skipping DB connection.")
        return None

def ensure_icd10_table(conn):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS icd10_codes (
        code TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        synonyms TEXT,
        search_text TEXT NOT NULL
    );
    """
    with conn.cursor() as cur:
        cur.execute(create_table_sql)
        conn.commit()
    print("Table 'icd10_codes' ensured in PostgreSQL.")

def upsert_icd10_codes(conn, df):
    insert_sql = """
    INSERT INTO icd10_codes (code, title, description, synonyms, search_text)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (code) DO UPDATE SET
        title=EXCLUDED.title,
        description=EXCLUDED.description,
        synonyms=EXCLUDED.synonyms,
        search_text=EXCLUDED.search_text;
    """
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(
                insert_sql,
                (
                    row.get("code"),
                    row.get("title"),
                    row.get("description"),
                    row.get("synonyms"),
                    row.get("search_text"),
                )
            )
        conn.commit()
    print(f"Inserted/updated {len(df)} rows into icd10_codes table.")
