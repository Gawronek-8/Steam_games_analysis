

import argparse
import copy
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATASETS = {
    "top_games": {
        "query": ROOT / "scripts" / "query_top_games.json",
        "raw_dir": ROOT / "data" / "raw" / "top_games",
        "csv": ROOT / "data" / "steam_top_games.csv",
        "limit": 50_000,
    },
    "upcoming_games": {
        "query": ROOT / "scripts" / "query_upcoming_games.json",
        "raw_dir": ROOT / "data" / "raw" / "upcoming_games",
        "csv": ROOT / "data" / "steam_upcoming_games.csv",
        "limit": 30_000,
    },
}

ENDPOINT = "https://api.steampowered.com/IStoreQueryService/Query/v1/"
INTERVALS = [60, 120, 300] 
MAX_ATTEMPTS_AT_SLOWEST = 5


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def page_path(raw_dir, start):
    return raw_dir / f"page_{start:06d}.json"


def fetch_page(base_query, start):
    body = copy.deepcopy(base_query)
    body["query"]["start"] = start
    input_json = json.dumps(body, separators=(",", ":"))
    resp = requests.get(ENDPOINT, params={"input_json": input_json}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if "response" not in data or "metadata" not in data["response"]:
        raise ValueError(f"unexpected response shape: {str(data)[:200]}")
    return {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "endpoint": ENDPOINT,
        "input_json": body,
        "url": resp.url,
        "response": data,
    }


def download(cfg, limit):
    base_query = json.loads(cfg["query"].read_text(encoding="utf-8"))
    page_size = base_query["query"]["count"]
    raw_dir = cfg["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    level = 0
    attempts_at_slowest = 0
    start = 0
    first_request = True
    while start < limit:
        path = page_path(raw_dir, start)
        if path.exists():
            items = json.loads(path.read_text(encoding="utf-8"))["response"]["response"].get("store_items", [])
            log(f"start={start}: already downloaded ({len(items)} items), skipping")
            if len(items) < page_size:
                break
            start += page_size
            continue

        if not first_request:
            time.sleep(INTERVALS[level])
        first_request = False

        try:
            page = fetch_page(base_query, start)
        except (requests.RequestException, ValueError) as e:
            if level < len(INTERVALS) - 1:
                level += 1
                log(f"start={start}: error ({e}); slowing down to one request every {INTERVALS[level]} s")
            else:
                attempts_at_slowest += 1
                log(f"start={start}: error ({e}); attempt {attempts_at_slowest}/{MAX_ATTEMPTS_AT_SLOWEST} at {INTERVALS[level]} s")
                if attempts_at_slowest >= MAX_ATTEMPTS_AT_SLOWEST:
                    log("giving up for now; run the script again later to resume")
                    return False
            continue

        attempts_at_slowest = 0
        path.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
        meta = page["response"]["response"]["metadata"]
        items = page["response"]["response"].get("store_items", [])
        log(f"start={start}: saved {len(items)} items (total matching: {meta.get('total_matching_records')})")
        if len(items) < page_size:
            log("last page reached")
            break
        start += page_size
    return True


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


def build_csv(cfg):
    csv_file = cfg["csv"]
    rows = []
    for path in sorted(cfg["raw_dir"].glob("page_*.json")):
        page = json.loads(path.read_text(encoding="utf-8"))
        start = page["input_json"]["query"]["start"]
        for i, item in enumerate(page["response"]["response"].get("store_items", [])):
            row = {"rank": start + i + 1, "page_start": start, "fetched_at_utc": page["fetched_at_utc"]}
            row.update(flatten(item))
            rows.append(row)
    if not rows:
        log("no raw pages found, CSV not written")
        return

    columns = ["rank", "page_start", "fetched_at_utc"]
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)

    csv_file.parent.mkdir(parents=True, exist_ok=True)
    with csv_file.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    log(f"CSV written: {csv_file} ({len(rows)} rows, {len(columns)} columns)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", choices=DATASETS, default="top_games", help="which query to run (default top_games)")
    parser.add_argument("--limit", type=int, help="how many games to download (default depends on --dataset)")
    parser.add_argument("--csv-only", action="store_true", help="only rebuild the CSV from saved raw pages")
    args = parser.parse_args()

    cfg = DATASETS[args.dataset]
    ok = True
    if not args.csv_only:
        ok = download(cfg, args.limit or cfg["limit"])
    build_csv(cfg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
