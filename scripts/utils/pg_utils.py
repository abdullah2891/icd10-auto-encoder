# utils/pg_utils.py
"""
PostgreSQL utility functions for ICD10 indexer
"""
import psycopg2

from pgvector.psycopg2 import register_vector
def register_vector_type(conn):
    """
    Register the pgvector extension with the PostgreSQL connection.
    """
    register_vector(conn)
    print("pgvector type registered.")



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
    # 1. Create extension if not exists and commit
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
    print("pgvector extension ensured.")

    # 2. Register vector type
    register_vector_type(conn)

    # 3. Create tables and index
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS icd10_codes (
        code TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        synonyms TEXT,
        search_text TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS icd10_meta (
        code TEXT PRIMARY KEY,
        embedding VECTOR(384) NOT NULL,
        CONSTRAINT fk_code FOREIGN KEY(code) REFERENCES icd10_codes(code) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_icd10_meta_embedding_hnsw
    ON icd10_meta USING hnsw (embedding vector_cosine_ops);
    """
    with conn.cursor() as cur:
        cur.execute(create_table_sql)
        conn.commit()
    print("Tables 'icd10_codes' and 'icd10_meta' ensured in PostgreSQL.")


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
    meta_sql = """
    INSERT INTO icd10_meta (code, embedding)
    VALUES (%s, %s)
    ON CONFLICT (code) DO UPDATE SET
        embedding=EXCLUDED.embedding;
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
            # Insert/update meta table if embedding is present
            if "embedding" in row and row["embedding"] is not None:
                cur.execute(
                    meta_sql,
                    (
                        row.get("code"),
                        row.get("embedding"),
                    )
                )
        conn.commit()
    print(f"Inserted/updated {len(df)} rows into icd10_codes and icd10_meta tables.")
