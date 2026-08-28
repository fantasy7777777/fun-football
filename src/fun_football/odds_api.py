"""Minimal read-only client for The Odds API.

The API key is read from the local ODDS_API_KEY environment variable and is
never included in logs or returned by this module.
"""

import json
import os
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .schema import Event, Market, PriceQuote


BASE_URL = "https://api.the-odds-api.com/v4"
_ODDS_CACHE: dict[tuple[str, str, str], tuple[float, list[tuple[Event, Market, PriceQuote]]]] = {}
_CACHE_SECONDS = 60


def _country_for_sport_key(sport_key: str) -> str:
    """Map the provider's competition key to a display country."""
    if sport_key.startswith("aussierules_") or sport_key.startswith("soccer_australia_"):
        return "Australia"
    country_by_key = {
        "soccer_epl": "England",
        "soccer_germany_bundesliga": "Germany",
        "soccer_italy_serie_a": "Italy",
        "soccer_spain_la_liga": "Spain",
        "soccer_france_ligue_one": "France",
        "soccer_usa_mls": "United States",
    }
    return country_by_key.get(sport_key, "International")


def _load_local_env() -> None:
    """Load simple KEY=value entries from .env without adding a dependency."""
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class OddsApiError(RuntimeError):
    """Raised when the provider request cannot be completed."""


class TheOddsApiClient:
    """Read-only client for upcoming and live odds."""

    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL) -> None:
        _load_local_env()
        self._api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self._api_key:
            raise OddsApiError("ODDS_API_KEY is not configured")
        self._base_url = base_url.rstrip("/")

    def get_odds(
        self,
        sport_key: str = "soccer_australia_aleague",
        regions: str = "au",
        markets: str = "h2h",
        force_refresh: bool = False,
    ) -> list[tuple[Event, Market, PriceQuote]]:
        """Fetch and normalise current odds for one sport key."""
        cache_key = (sport_key, regions, markets)
        cached = _ODDS_CACHE.get(cache_key)
        if cached and not force_refresh and time.monotonic() - cached[0] < _CACHE_SECONDS:
            return cached[1]
        query = urlencode({"apiKey": self._api_key, "regions": regions, "markets": markets})
        request = Request(
            f"{self._base_url}/sports/{sport_key}/odds/?{query}",
            headers={"Accept": "application/json", "User-Agent": "FunFootball/0.1"},
        )
        try:
            with urlopen(request, timeout=8) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise OddsApiError(f"provider returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise OddsApiError("provider request failed") from exc

        records = self._normalise(payload, sport_key)
        _ODDS_CACHE[cache_key] = (time.monotonic(), records)
        return records

    @staticmethod
    def _normalise(payload: list[dict], sport_key: str) -> list[tuple[Event, Market, PriceQuote]]:
        records: list[tuple[Event, Market, PriceQuote]] = []
        for item in payload:
            event_id = str(item["id"])
            source = "the-odds-api"
            event = Event(
                event_id=event_id,
                sport="football",
                country=_country_for_sport_key(sport_key),
                competition=item.get("sport_title") or sport_key,
                home_team=item["home_team"],
                away_team=item["away_team"],
                start_time=datetime.fromisoformat(item["commence_time"].replace("Z", "+00:00")),
                source=source,
                source_event_id=event_id,
            )
            observed_at = datetime.now().astimezone()
            for bookmaker in item.get("bookmakers", []):
                bookmaker_key = bookmaker["key"]
                for api_market in bookmaker.get("markets", []):
                    market_key = api_market["key"]
                    market_id = f"{event_id}:{bookmaker_key}:{market_key}"
                    market = Market(
                        market_id=market_id,
                        event_id=event_id,
                        market_type=market_key,
                        source=source,
                        source_market_id=f"{bookmaker_key}:{market_key}",
                        source_name=bookmaker.get("title") or bookmaker_key,
                    )
                    quote_time = datetime.fromisoformat(
                        (api_market.get("last_update") or bookmaker.get("last_update")
                         or item["commence_time"]).replace("Z", "+00:00")
                    )
                    for outcome in api_market.get("outcomes", []):
                        records.append((event, market, PriceQuote(
                            quote_id=f"{market_id}:{outcome['name']}",
                            market_id=market_id,
                            outcome=outcome["name"],
                            price=Decimal(str(outcome["price"])),
                            observed_at=quote_time or observed_at,
                            source=source,
                            currency="AUD",
                        )))
        return records
