"""Download current Steam prices per country from the store appdetails endpoint to raw JSON and CSV.

At the end all responses are combined into data/steam_current_prices.csv, one row per game x country:

    appid, country_code, status, currency, price, initial, price_dsc, fetched_date

`status` says why a row has or has not a price:
    priced          price_overview present
    no_price        success: true, but no price (free to play or not purchasable)
    not_available   success: false, the game is not sold in this country (region lock)
`price` is the current price and `initial` the regular price, both in `currency`
and divided by 100
"""

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from fetch_top_games import log

ROOT = Path(__file__).resolve().parent.parent
QUERY_FILE = ROOT / "scripts" / "query_current_prices.json"
RAW_DIR = ROOT / "data" / "raw" / "current_prices"
CSV_FILE = ROOT / "data" / "steam_current_prices.csv"
CSV_COLS = ["appid", "country_code", "status", "currency", "price", "initial", "price_dsc", "fetched_date"]

URL = "https://store.steampowered.com/api/appdetails"
BACKOFF = [60, 120, 300] 
_last_request = 0.0


def request(params, spacing):
    """GET appdetails at most once per `spacing` seconds; wait and retry while the store API throttles."""
    global _last_request
    failures = 0
    while True:
        time.sleep(max(0.0, _last_request + spacing - time.monotonic()))
        _last_request = time.monotonic()
        try:
            resp = requests.get(URL, params=params, timeout=60)
        except (requests.ConnectionError, requests.Timeout) as e:
            wait = BACKOFF[min(failures, len(BACKOFF) - 1)]
            failures += 1
            log(f"connection error ({type(e).__name__}), waiting {wait} s")
            time.sleep(wait)
            continue
        if resp.status_code in (403, 429) or (resp.ok and resp.json() is None):
            wait = int(resp.headers.get("Retry-After", BACKOFF[min(failures, len(BACKOFF) - 1)]))
            failures += 1
            log(f"throttled (HTTP {resp.status_code}), waiting {wait} s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp


def top_appids(settings):
    appids, seen = [], set()
    limit = settings["top_n_games"]
    with (ROOT / settings["games_source_csv"]).open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["appid"] and row["appid"] not in seen:
                seen.add(row["appid"])
                appids.append(row["appid"])
            if limit is not None and len(appids) >= limit:
                break
    return appids


def download(settings):
    appids = top_appids(settings)
    size = settings["batch_size"]
    batches = [appids[i:i + size] for i in range(0, len(appids), size)]
    spacing = 300 / settings["requests_per_5_min"]
    total = len(batches) * len(settings["countries"])
    log(f"{len(appids)} games in {len(batches)} batches x {len(settings['countries'])} countries = {total} requests")

    done = 0
    for country in settings["countries"]:
        country_dir = RAW_DIR / country
        country_dir.mkdir(parents=True, exist_ok=True)
        for i, batch in enumerate(batches):
            done += 1
            out = country_dir / f"batch_{i:05d}.json"
            if out.exists():
                continue
            params = {"appids": ",".join(batch), "cc": country, "filters": settings["filters"]}
            resp = request(params, spacing)
            record = {
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "url": resp.url,
                "country": country,
                "appids": batch,
                "response": resp.json(),
            }
            out.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            if done % 50 == 0:
                log(f"prices: {done}/{total} requests done")
    log(f"prices: {total}/{total} done")


def build_csv():
    """Combine all raw batches into one row per game x country."""
    rows = priced = 0
    with CSV_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLS)
        for path in sorted(RAW_DIR.glob("*/batch_*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            fetched_date = record["fetched_at_utc"][:10]
            for appid in record["appids"]:
                entry = record["response"].get(appid) or {}
                data = entry.get("data")
                price = data.get("price_overview") if isinstance(data, dict) else None
                if not entry.get("success"):
                    writer.writerow([appid, record["country"], "not_available", "", "", "", "", fetched_date])
                elif price:
                    writer.writerow([
                        appid,
                        record["country"],
                        "priced",
                        price["currency"],
                        price["final"] / 100,
                        price["initial"] / 100,
                        price["discount_percent"],
                        fetched_date,
                    ])
                    priced += 1
                else:
                    writer.writerow([appid, record["country"], "no_price", "", "", "", "", fetched_date])
                rows += 1
    log(f"CSV written: {CSV_FILE} ({rows} game x country rows, {priced} with a price)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv-only", action="store_true", help="only rebuild the CSV from saved raw files")
    args = parser.parse_args()
    if not args.csv_only:
        download(json.loads(QUERY_FILE.read_text(encoding="utf-8")))
    build_csv()


if __name__ == "__main__":
    main()
