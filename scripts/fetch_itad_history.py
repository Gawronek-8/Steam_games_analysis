

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from fetch_top_games import log
from settings import Settings

ROOT = Path(__file__).resolve().parent.parent
QUERY_FILE = ROOT / "scripts" / "query_itad_history.json"
RAW_DIR = ROOT / "data" / "raw" / "itad"
LOOKUP_DIR = RAW_DIR / "lookup"
HISTORY_DIR = RAW_DIR / "history"
JSON_FILE = ROOT / "data" / "itad_price_history.json"

BASE = "https://api.isthereanydeal.com"
_last_request = 0.0


def redact(url, key):
    return url.replace(key, "REDACTED") if key else url


def interval(settings):
    return 300 / settings["requests_per_5_min"]


def request(method, url, key, spacing, params=None, **kwargs):
    global _last_request
    while True:
        time.sleep(max(0.0, _last_request + spacing - time.monotonic()))
        _last_request = time.monotonic()
        resp = requests.request(method, url, params={"key": key, **(params or {})}, timeout=60, **kwargs)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 60))
            log(f"rate limited (429), waiting {wait} s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp


def top_appids(settings):
    appids, seen = [], set()
    with (ROOT / settings["games_source_csv"]).open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["appid"] and row["appid"] not in seen:
                seen.add(row["appid"])
                appids.append(row["appid"])
            if len(appids) >= settings["top_n_games"]:
                break
    return appids


def lookup_ids(appids, settings, key):
    LOOKUP_DIR.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for path in LOOKUP_DIR.glob("batch_*.json"):
        for shop_id, itad_id in json.loads(path.read_text(encoding="utf-8"))["response"].items():
            mapping[shop_id.removeprefix("app/")] = itad_id

    missing = [a for a in appids if a not in mapping]
    size = settings["lookup_batch_size"]
    for i in range(0, len(missing), size):
        batch = missing[i:i + size]
        body = [f"app/{a}" for a in batch]
        resp = request("POST", f"{BASE}/lookup/id/shop/61/v1", key, interval(settings), json=body)
        record = {
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "url": redact(resp.url, key),
            "request_body": body,
            "response": resp.json(),
        }
        out = LOOKUP_DIR / f"batch_{datetime.now():%Y%m%d_%H%M%S}_{i:05d}.json"
        out.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        for shop_id, itad_id in record["response"].items():
            mapping[shop_id.removeprefix("app/")] = itad_id
        log(f"lookup: {i + len(batch)}/{len(missing)} appids mapped")
    return mapping


def download(settings, key):
    appids = top_appids(settings)
    mapping = lookup_ids(appids, settings, key)
    found = [a for a in appids if mapping.get(a)]
    log(f"{len(found)}/{len(appids)} games found on ITAD")

    total = len(found) * len(settings["countries"])
    done = 0
    for country in settings["countries"]:
        country_dir = HISTORY_DIR / country
        country_dir.mkdir(parents=True, exist_ok=True)
        for appid in found:
            done += 1
            out = country_dir / f"{appid}.json"
            if out.exists():
                continue
            params = {
                "id": mapping[appid],
                "country": country,
                "shops": ",".join(str(s) for s in settings["shops"]),
                "since": settings["since"],
            }
            resp = request("GET", f"{BASE}/games/history/v2", key, interval(settings), params=params)
            record = {
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "url": redact(resp.url, key),
                "appid": appid,
                "itad_id": mapping[appid],
                "country": country,
                "response": resp.json(),
            }
            out.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            if done % 100 == 0:
                log(f"history: {done}/{total} requests done")
    log(f"history: {total}/{total} done")


def build_json():
    records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(HISTORY_DIR.glob("*/*.json"))]
    if not records:
        log("no history files found, JSON not written")
        return
    JSON_FILE.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    entries = sum(len(r["response"]) for r in records)
    log(f"JSON written: {JSON_FILE} ({len(records)} game x country records, {entries} price changes)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json-only", action="store_true", help="only rebuild the combined JSON from saved raw files")
    args = parser.parse_args()
    if not args.json_only:
        settings = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
        key = Settings().itad_key
        if not key:
            raise SystemExit("ITAD_KEY is empty: put your key in .env")
        download(settings, key)
    build_json()


if __name__ == "__main__":
    main()
