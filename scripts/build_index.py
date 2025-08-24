# ============================================================================
# File: scripts/build_index.py
# ============================================================================
# Usage: python scripts/build_index.py --csv data/icd10_sample.csv --out data/index


if __name__ == "__main__":
    import argparse, os, json, pickle, pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer


    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()


    os.makedirs(args.out, exist_ok=True)
    df = pd.read_csv(args.csv)


    def mk_search(row):
        parts = [str(row.get("title", "")), str(row.get("description", "")), str(row.get("synonyms", ""))]
        return " \n ".join([p for p in parts if p and p != "nan"]).lower()


    df["search_text"] = df.apply(mk_search, axis=1)


    vec = TfidfVectorizer(ngram_range=(1,2), min_df=1)
    X = vec.fit_transform(df["search_text"].tolist())


    with open(os.path.join(args.out, "codes_meta.json"), "w") as f:
        json.dump(df[["code","title","description"]].to_dict(orient="records"), f)
    with open(os.path.join(args.out, "tfidf_vectorizer.pkl"), "wb") as f:
        pickle.dump(vec, f)
    with open(os.path.join(args.out, "tfidf_matrix.pkl"), "wb") as f:
        pickle.dump(X, f)


    print(f"Index built at {args.out}")