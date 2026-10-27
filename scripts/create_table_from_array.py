from pathlib import Path
import csv
import json

ROOT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = ROOT_DIR / "data"
TARGET_CSV = DATA_DIR / "steam_upcoming_games.csv"
TARGET_COLUMN = 'tagids'
KEY_COLUMN = 'appid'
OUTPUT_CSV = DATA_DIR / "steam_upcoming_games_tags.csv"
_OUTPUT_COLS = ['game_id', 'tag_id']


def _create_table_from_array():
    with open(TARGET_CSV, 'r', encoding='utf-8-sig', newline="") as r, \
        open(OUTPUT_CSV, 'w', encoding='utf-8', newline="") as w:
        reader = csv.DictReader(r)
        writer = csv.writer(w)
        writer.writerow(_OUTPUT_COLS)

        for entry in reader:
            for element in json.loads(entry[TARGET_COLUMN] or '[]'):
                writer.writerow([entry[KEY_COLUMN], element])


if __name__ == "__main__":
    _create_table_from_array()
