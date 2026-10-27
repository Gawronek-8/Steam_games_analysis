

import argparse
import csv
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from fetch_top_games import log

ROOT = Path(__file__).resolve().parent.parent
QUERY_FILE = ROOT / "scripts" / "query_nbp_rates.json"
RAW_DIR = ROOT / "data" / "raw" / "nbp"
OUT_DIR = ROOT / "data"

BASE = "https://api.nbp.pl/api/exchangerates/tables"
PAUSE_SECONDS = 1


def date_chunks(start, end, max_days):
    while start <= end:
        chunk_end = min(start + timedelta(days=max_days - 1), end)
        yield start, chunk_end
        start = chunk_end + timedelta(days=1)


def download(settings):
    start = date.fromisoformat(settings["start_date"])
    end = date.fromisoformat(settings["end_date"]) if settings["end_date"] else date.today()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for table in settings["tables"]:
        for chunk_start, chunk_end in date_chunks(start, end, settings["max_days_per_request"]):
            url = f"{BASE}/{table}/{chunk_start}/{chunk_end}/"
            resp = requests.get(url, params={"format": "json"}, timeout=60)
            if resp.status_code == 404: 
                data = []
            else:
                resp.raise_for_status()
                data = resp.json()
            record = {
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "url": resp.url,
                "status_code": resp.status_code,
                "response": data,
            }
            out = RAW_DIR / f"table_{table}_{chunk_start}_{chunk_end}.json"
            out.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            log(f"table {table} {chunk_start}..{chunk_end}: {len(data)} publications")
            time.sleep(PAUSE_SECONDS)


def build_csv(table):
    rows = []
    for path in sorted(RAW_DIR.glob(f"table_{table}_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        for publication in record["response"]:
            for rate in publication["rates"]:
                rows.append({
                    "fetched_at_utc": record["fetched_at_utc"],
                    "table": publication["table"],
                    "no": publication["no"],
                    "effectiveDate": publication["effectiveDate"],
                    **rate,
                })
    out = OUT_DIR / f"nbp_rates_table_{table}.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    log(f"CSV written: {out} ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv-only", action="store_true", help="only rebuild CSVs from saved raw files")
    args = parser.parse_args()
    settings = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
    if not args.csv_only:
        download(settings)
    for table in settings["tables"]:
        build_csv(table)


if __name__ == "__main__":
    main()
