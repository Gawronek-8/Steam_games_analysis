"""Create game x category bridge tables
"""

import csv
import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = ROOT_DIR / "data"
KEY_COLUMN = 'appid'
CATEGORY_COLUMNS = [
    'categories.supported_player_categoryids',
    'categories.feature_categoryids',
    'categories.controller_categoryids',
]
JOBS = [ 
    (DATA_DIR / "steam_top_games.csv", DATA_DIR / "steam_top_games_categories.csv"),
    (DATA_DIR / "steam_upcoming_games.csv", DATA_DIR / "steam_upcoming_games_categories.csv"),
]
_OUTPUT_COLS = ['game_id', 'category_id']


def _create_category_bridge(source_csv, output_csv):
    rows = 0
    with open(source_csv, 'r', encoding='utf-8-sig', newline="") as r, \
            open(output_csv, 'w', encoding='utf-8', newline="") as w:
        reader = csv.DictReader(r)
        writer = csv.writer(w)
        writer.writerow(_OUTPUT_COLS)

        for entry in reader:
            for column in CATEGORY_COLUMNS:
                for category_id in json.loads(entry.get(column) or '[]'):
                    writer.writerow([entry[KEY_COLUMN], category_id])
                    rows += 1
    print(f"{output_csv.name}: {rows} rows")


if __name__ == "__main__":
    for source, output in JOBS:
        _create_category_bridge(source, output)
