"""
ICD10 Wikipedia Description Fetcher & Synonym Extractor

Usage:
    # Fetch Wikipedia descriptions for ICD10 codes
    python build_data_set.py --input INPUT.csv --output OUTPUT.csv

    # Extract synonyms (symptoms) from description using local API
    python build_data_set.py --input INPUT.csv --output OUTPUT.csv --extract-synonyms

    # Optionally specify model (default: llama3.2:1b)
    python build_data_set.py --input INPUT.csv --output OUTPUT.csv --extract-synonyms --model llama3.2:1b

Options:
    --input, -i      Path to input CSV file containing titles (first column used)
    --output, -o     Path to output CSV file (will contain columns: title, description, or synonym)
    --extract-synonyms  Extract symptoms from description and add as 'synonym' column
    --model          Model name for synonym extraction (default: llama3.2:1b)

Output:
    - For --extract-synonyms, adds a 'synonym' column (lowercase) to output file
    - Rows with empty description are skipped and written to 'icd_10_code_without_any_description.csv'

Example:
    python build_data_set.py -i icd10_sample.csv -o icd10_descriptions.csv
    python build_data_set.py -i icd10_sample.csv -o icd10_synonyms.csv --extract-synonyms
    python build_data_set.py -i icd10_sample.csv -o icd10_synonyms.csv --extract-synonyms --model llama3.2:1b
"""
import time, requests
import argparse
import csv
import sys

UA = "ICD10-DescFetcher/0.1 (+https://github.com/abdullah2891/icd10-auto-encoder)"
S = requests.Session()
S.headers.update({"User-Agent": UA})

def wiki_summary_batch(titles):
    params = {
        "action": "query", "prop": "extracts",
        "exintro": 1, "explaintext": 1, "redirects": 1,
        "format": "json", "maxlag": 5,
        "titles": "|".join(titles)
    }
    for attempt in range(5):
        r = S.get("https://en.wikipedia.org/w/api.php", params=params, timeout=30)
        # polite backoff
        if r.status_code in (429, 503):
            delay = int(r.headers.get("Retry-After", "5"))
            time.sleep(min(delay, 60))
            continue
        data = r.json()
        # Handle maxlag error
        if "error" in data and data["error"].get("code") == "maxlag":
            time.sleep(5)
            continue
        # Log other API errors as warnings and continue
        if "error" in data and data["error"].get("code") != "maxlag":
            print(f"Warning: API error for batch: {data['error']}", file=sys.stderr)
            return {"query": {"pages": {}}}  # Return empty result for this batch
        return data
    raise RuntimeError("Too many retries/backoffs")
def extract_synonyms(input_file, output_file, model_name="llama3.2:1b"):
    # Read input file
    print(f"[INFO] Reading input file: {input_file}")
    input_rows = []
    with open(input_file, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        if not set(['code', 'title', 'description']).issubset(reader.fieldnames):
            print("Input file must have 'code', 'title', and 'description' columns.", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            input_rows.append(row)

    print(f"[INFO] Extracting synonyms using model: {model_name}")
    output_rows = []
    no_desc_rows = []
    total = len(input_rows)
    for idx, row in enumerate(input_rows, 1):
        desc = row.get('description', '').strip()
        if not desc:
            print(f"[WARN] Skipping code {row.get('code')} (no description)")
            no_desc_rows.append(row)
            continue
        print(f"[INFO] ({idx}/{total}) Extracting for code: {row.get('code')}, title: {row.get('title')}")
        try:
            payload = {
                "model": model_name,
                "prompt": f"Extract symptoms separated by semicolon from the following description: {desc} only list symtoms, no other text.",
                "stream": False
            }
            print(f"[DEBUG] API request payload: {payload}")
            r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
            r.raise_for_status()
            result = r.json()
            print(f"[DEBUG] API response: {result}")
            symptoms = result.get('response', '').strip().lower()
            print(f"[INFO] Extracted synonyms: {symptoms}")
        except Exception as e:
            print(f"[ERROR] Extracting synonyms for code {row.get('code')}: {e}", file=sys.stderr)
            symptoms = ''
        row['synonym'] = symptoms
        output_rows.append(row)

    print(f"[INFO] Writing output file: {output_file} (rows: {len(output_rows)})")
    fieldnames = list(input_rows[0].keys()) + ['synonym'] if 'synonym' not in input_rows[0] else list(input_rows[0].keys())
    with open(output_file, "w", newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    if no_desc_rows:
        print(f"[INFO] Writing codes without description to icd_10_code_without_any_description.csv (rows: {len(no_desc_rows)})")
        with open("icd_10_code_without_any_description.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in no_desc_rows:
                writer.writerow(row)
    print(f"[INFO] Synonym extraction complete. Total processed: {total}, with description: {len(output_rows)}, without description: {len(no_desc_rows)}")

    # Write output file with synonym column
    fieldnames = list(input_rows[0].keys()) + ['synonym'] if 'synonym' not in input_rows[0] else list(input_rows[0].keys())
    with open(output_file, "w", newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    # Write codes without description to separate file
    if no_desc_rows:
        with open("icd_10_code_without_any_description.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in no_desc_rows:
                writer.writerow(row)

    
def main():
    parser = argparse.ArgumentParser(description="Fetch Wikipedia descriptions for ICD10 codes or extract synonyms.")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file with titles (one per line or column)")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file")
    parser.add_argument("--extract-synonyms", action="store_true", help="Extract synonyms from description using local API")
    parser.add_argument("--model", type=str, default="llama3.2:1b", help="Model name for synonym extraction (default: llama3.2:1b)")
    args = parser.parse_args()

    if args.extract_synonyms:
        extract_synonyms(args.input, args.output, model_name=args.model)
        return

    # Read and validate input file for 'code' and 'title' columns
    input_rows = []
    with open(args.input, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        if not set(['code', 'title']).issubset(reader.fieldnames):
            print("Input file must have 'code' and 'title' columns.", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            if row['code'] and row['title']:
                input_rows.append({'code': row['code'], 'title': row['title']})
    if not input_rows:
        print("No valid rows found in input file.", file=sys.stderr)
        sys.exit(1)

    # Fetch descriptions in batches (Wikipedia API limit: ~50 titles per request)
    batch_size = 50
    title_to_desc = {}
    titles = [row['title'] for row in input_rows]
    for i in range(0, len(titles), batch_size):
        batch = titles[i:i+batch_size]
        try:
            data = wiki_summary_batch(batch)
        except Exception as e:
            print(f"Error fetching batch {i//batch_size+1}: {e}", file=sys.stderr)
            sys.exit(1)
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            title = page.get("title", "")
            desc = page.get("extract", "")
            if not desc:
                print(f"Warning: No description found for title '{title}'", file=sys.stderr)
            title_to_desc[title] = desc

    # Write results to output file with code, title, description columns
    with open(args.output, "w", newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=["code", "title", "description"])
        writer.writeheader()
        for row in input_rows:
            writer.writerow({
                "code": row["code"],
                "title": row["title"],
                "description": title_to_desc.get(row["title"], "")
            })

if __name__ == "__main__":
    main()

