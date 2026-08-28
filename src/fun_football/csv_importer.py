"""Import manually prepared market observations from CSV."""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .schema import Event, Market, PriceQuote


REQUIRED_COLUMNS = {
    "event_id", "sport", "country", "competition", "home_team", "away_team",
    "start_time", "event_source", "market_id", "market_type", "is_live",
    "quote_id", "outcome", "price", "observed_at", "quote_source",
}


def _timestamp(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp: {value}") from exc


def _boolean(value: str, field: str) -> bool:
    normalised = value.strip().casefold()
    if normalised not in {"true", "false"}:
        raise ValueError(f"{field} must be true or false")
    return normalised == "true"


def load_market_csv(path: str | Path) -> list[tuple[Event, Market, PriceQuote]]:
    """Load validated event, market, and quote records from a CSV file."""

    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        records = []
        for row_number, row in enumerate(reader, start=2):
            try:
                event = Event(
                    event_id=row["event_id"], sport=row["sport"], country=row["country"],
                    competition=row["competition"], home_team=row["home_team"],
                    away_team=row["away_team"], start_time=_timestamp(row["start_time"], "start_time"),
                    source=row["event_source"],
                )
                market = Market(
                    market_id=row["market_id"], event_id=event.event_id,
                    market_type=row["market_type"], source=row["quote_source"],
                    is_live=_boolean(row["is_live"], "is_live"),
                )
                quote = PriceQuote(
                    quote_id=row["quote_id"], market_id=market.market_id,
                    outcome=row["outcome"], price=Decimal(row["price"]),
                    observed_at=_timestamp(row["observed_at"], "observed_at"),
                    source=row["quote_source"], currency=row.get("currency") or "AUD",
                    source_url=row.get("source_url") or None,
                )
                records.append((event, market, quote))
            except (KeyError, ValueError, ArithmeticError) as exc:
                raise ValueError(f"Invalid CSV row {row_number}: {exc}") from exc

    return records
