
import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from fetch_top_games import flatten, log

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "steam_dictionaries"
OUT_DIR = ROOT / "data"

DICTIONARIES = {
    "tags": {
        "url": "https://api.steampowered.com/IStoreService/GetTagList/v1/",
        "query": ROOT / "scripts" / "query_tags.json",
        "list_key": "tags",
    },
    "categories": {
        "url": "https://api.steampowered.com/IStoreBrowseService/GetStoreCategories/v1/",
        "query": ROOT / "scripts" / "query_categories.json",
        "list_key": "categories",
    },
}


def download(name, cfg):
    body = json.loads(cfg["query"].read_text(encoding="utf-8"))
    resp = requests.get(cfg["url"], params={"input_json": json.dumps(body, separators=(",", ":"))}, timeout=60)
    resp.raise_for_status()
    record = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "endpoint": cfg["url"],
        "input_json": body,
        "url": resp.url,
        "response": resp.json(),
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"{name}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    log(f"{name}: saved {len(record['response']['response'][cfg['list_key']])} entries")


def build_csv(name, cfg):
    record = json.loads((RAW_DIR / f"{name}.json").read_text(encoding="utf-8"))
    rows = [{"fetched_at_utc": record["fetched_at_utc"], **flatten(item)}
            for item in record["response"]["response"][cfg["list_key"]]]
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    out = OUT_DIR / f"steam_{name}.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    log(f"CSV written: {out} ({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv-only", action="store_true", help="only rebuild CSVs from saved raw files")
    args = parser.parse_args()
    for name, cfg in DICTIONARIES.items():
        if not args.csv_only:
            download(name, cfg)
            time.sleep(2)
        build_csv(name, cfg)


if __name__ == "__main__":
    main()
