

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "worldbank"
OUT_DIR = ROOT / "data"

BASE = "https://api.worldbank.org/v2"
INDICATORS = {
    "NY.GDP.PCAP.PP.CD": "worldbank_gdp_per_capita_ppp",
    "NY.GNP.PCAP.PP.CD": "worldbank_gni_per_capita_ppp",
}
YEARS = (2023, 2024, 2025) 
PER_PAGE = 20000
PAUSE_SECONDS = 2


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def fetch_all_pages(path, params, raw_prefix):
    """Fetch every page of a World Bank list endpoint and save each response as returned."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    page = 1
    while True:
        query = {**params, "format": "json", "per_page": PER_PAGE, "page": page}
        resp = requests.get(f"{BASE}/{path}", params=query, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        record = {
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "url": resp.url,
            "response": data,
        }
        out = RAW_DIR / f"{raw_prefix}_page_{page:03d}.json"
        out.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        meta = data[0]
        log(f"{path}: page {meta['page']}/{meta['pages']} saved ({len(data[1] or [])} records, total {meta['total']})")
        if meta["page"] >= meta["pages"]:
            break
        page += 1
        time.sleep(PAUSE_SECONDS)


def flatten(value, prefix=""):
    out = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out.update(flatten(v, f"{prefix}{k}."))
    elif isinstance(value, list):
        out[prefix[:-1]] = json.dumps(value, ensure_ascii=False)
    else:
        out[prefix[:-1]] = value
    return out


def build_csv(raw_prefix, csv_name):
    rows = []
    for path in sorted(RAW_DIR.glob(f"{raw_prefix}_page_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        for item in record["response"][1] or []:
            row = {"fetched_at_utc": record["fetched_at_utc"]}
            row.update(flatten(item))
            rows.append(row)
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    out = OUT_DIR / f"{csv_name}.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    log(f"CSV written: {out} ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv-only", action="store_true", help="only rebuild CSVs from saved raw files")
    args = parser.parse_args()

    if not args.csv_only:
        for indicator, name in INDICATORS.items():
            fetch_all_pages(f"country/all/indicator/{indicator}", {}, name)
            time.sleep(PAUSE_SECONDS)
            for year in YEARS:
                fetch_all_pages(f"country/all/indicator/{indicator}", {"date": year}, f"{year}_{name}")
                time.sleep(PAUSE_SECONDS)
        fetch_all_pages("country", {}, "worldbank_countries")

    for name in INDICATORS.values():
        build_csv(name, name)
        for year in YEARS:
            build_csv(f"{year}_{name}", f"{year}_{name}")
    build_csv("worldbank_countries", "worldbank_countries")


if __name__ == "__main__":
    main()
