from pathlib import Path
import json
import csv
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

ROOT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = ROOT_DIR / "data"
ITAD_PRICES = DATA_DIR / "itad_price_history.json"
ITAD_PRICES_CSV = DATA_DIR / "itad_price_history.csv"
_REMOVED_PREFIX = 'deal_'


class _PriceRow(BaseModel):
    model_config = ConfigDict(extra='ignore')

    app_id: int = Field(validation_alias='appid')
    itad_id: str
    country: str
    timestamp: str | None = None
    shop: str | None = Field(None, validation_alias='shop_name')
    currency: str | None = Field(None, validation_alias='price_currency')
    regular_price: float | None = Field(None, validation_alias='regular_amount')
    regular_price_int: int | None = Field(None, validation_alias='regular_amountInt')
    cut: int | None = None
    deal_price: float | None = Field(None, validation_alias='price_amount')
    deal_price_int: int | None = Field(None, validation_alias='price_amountInt')


_CSV_COLS = list(_PriceRow.model_fields)


def _load_itad_prices():
    with open(ITAD_PRICES, 'r', encoding = 'utf-8') as prices, \
        open(ITAD_PRICES_CSV, 'w', encoding= 'utf-8', newline="") as w:
        prices = json.load(prices)

        writer = csv.DictWriter(w, _CSV_COLS)
        writer.writeheader()

        for price in prices:
            for offer in price["response"] or [{}]:
                row = _PriceRow.model_validate({**price, **_flatten_offer(offer)})
                writer.writerow(row.model_dump())


def _flatten(dictionary: Mapping, prefix: str = ''):
    fields = {}
    for k, v in dictionary.items():
        key = f'{prefix}{k}'
        if isinstance(v, Mapping):
            fields.update(_flatten(v, f'{key}_'))
        else:
            fields[key] = v
    return fields


def _flatten_offer(offer: Mapping):
    return {k.removeprefix(_REMOVED_PREFIX): v for k, v in _flatten(offer).items()}


if __name__ == "__main__":
    _load_itad_prices()
