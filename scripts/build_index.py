# ============================================================================
# File: scripts/build_index.py
# ============================================================================
# Usage: python scripts/build_index.py --csv data/icd10_sample.csv --out data/index
import sys
import argparse, os, json, pickle, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.text_utils import build_search_text
from utils.pg_utils import get_pg_connection, ensure_icd10_table, upsert_icd10_codes


if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
    from utils.text_utils import build_search_text

    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    # PostgreSQL connection arguments
    ap.add_argument("--pg-host", default=None, help="PostgreSQL host")
    ap.add_argument("--pg-port", default=5432, type=int, help="PostgreSQL port")
    ap.add_argument("--pg-user", default=None, help="PostgreSQL user")
    ap.add_argument("--pg-password", default=None, help="PostgreSQL password")
    ap.add_argument("--pg-dbname", default=None, help="PostgreSQL database name")
    args = ap.parse_args()

    # Connect to PostgreSQL using utility
    pg_conn = get_pg_connection(args)

    os.makedirs(args.out, exist_ok=True)
    df = pd.read_csv(args.csv)

    # Create table in PostgreSQL if connected
    if pg_conn is not None:
        ensure_icd10_table(pg_conn)


    df["search_text"] = df.apply(build_search_text, axis=1)

    # Insert rows into icd10_codes table if PostgreSQL connection is available
    if pg_conn is not None:
        upsert_icd10_codes(pg_conn, df)

    vec = TfidfVectorizer(ngram_range=(1,2), min_df=1)
    X = vec.fit_transform(df["search_text"].tolist())

    with open(os.path.join(args.out, "codes_meta.json"), "w") as f:
        json.dump(df[["code","title","description"]].to_dict(orient="records"), f)
    with open(os.path.join(args.out, "tfidf_vectorizer.pkl"), "wb") as f:
        pickle.dump(vec, f)
    with open(os.path.join(args.out, "tfidf_matrix.pkl"), "wb") as f:
        pickle.dump(X, f)

    print(f"Index built at {args.out}")