"""Read-only Betfair Exchange API client for market research.

This adapter deliberately exposes market discovery and price retrieval only.
It does not implement account, order, balance, or transaction operations.
"""

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .odds_api import _load_local_env


BETTING_API_URL = "https://api.betfair.com/exchange/betting/json-rpc/v1"
_MARKET_PRICE_CACHE: dict[str, tuple[float, list["BetfairRunnerPrice"]]] = {}
_CACHE_SECONDS = 60


class BetfairApiError(RuntimeError):
    """Raised when a read-only Betfair request cannot be completed."""


@dataclass(frozen=True)
class BetfairRunnerPrice:
    """A named Betfair runner with delayed or live exchange observations."""

    market_id: str
    selection_id: str
    runner_name: str
    status: str
    last_price_traded: Decimal | None
    available_to_back: Decimal | None
    available_to_lay: Decimal | None
    observed_at: datetime
    data_delayed: bool


def _first_price(levels) -> Decimal | None:
    if not levels:
        return None
    price = levels[0].get("price")
    return Decimal(str(price)) if price is not None else None


class BetfairExchangeClient:
    """Small authenticated client limited to Betfair read-only operations."""

    def __init__(
        self,
        app_key: str | None = None,
        session_token: str | None = None,
        api_url: str = BETTING_API_URL,
    ) -> None:
        _load_local_env()
        self._app_key = app_key or os.getenv("BETFAIR_APP_KEY")
        self._session_token = session_token or os.getenv("BETFAIR_SESSION_TOKEN")
        self._api_url = api_url
        if not self._app_key:
            raise BetfairApiError("BETFAIR_APP_KEY is not configured")
        if not self._session_token:
            raise BetfairApiError("BETFAIR_SESSION_TOKEN is not configured")

    def _call(self, method: str, params: dict) -> dict:
        payload = json.dumps([{
            "jsonrpc": "2.0",
            "method": f"SportsAPING/v1.0/{method}",
            "params": params,
            "id": 1,
        }]).encode("utf-8")
        request = Request(
            self._api_url,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Application": self._app_key,
                "X-Authentication": self._session_token,
                "User-Agent": "FunFootball/0.2-read-only",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                response_payload = json.load(response)
        except HTTPError as exc:
            raise BetfairApiError(f"provider returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise BetfairApiError("provider request failed") from exc
        if not response_payload or "result" not in response_payload[0]:
            error = response_payload[0].get("error", {}) if response_payload else {}
            raise BetfairApiError(error.get("errorCode", "provider returned an invalid response"))
        result = response_payload[0]["result"]
        if isinstance(result, dict) and result.get("status") == "FAILURE":
            raise BetfairApiError(result.get("errorCode", "provider rejected the request"))
        return result

    def list_market_catalogue(self, market_id: str) -> dict:
        """Return market metadata and runner names for one published market."""
        result = self._call("listMarketCatalogue", {
            "filter": {"marketIds": [market_id]},
            "marketProjection": ["RUNNER_DESCRIPTION", "MARKET_START_TIME"],
            "maxResults": 1,
        })
        if not result:
            raise BetfairApiError("market was not found")
        return result[0]

    def list_market_book(self, market_id: str) -> dict:
        """Return dynamic prices for one market; this never places an order."""
        result = self._call("listMarketBook", {
            "marketIds": [market_id],
            "priceProjection": {"priceData": ["EX_BEST_OFFERS", "SP_TRADED"]},
        })
        if not result:
            raise BetfairApiError("market book was not returned")
        return result[0]

    def get_market_prices(self, market_id: str, force_refresh: bool = False) -> list[BetfairRunnerPrice]:
        """Join catalogue runner names with the market book price observations."""
        cached = _MARKET_PRICE_CACHE.get(market_id)
        if cached and not force_refresh and time.monotonic() - cached[0] < _CACHE_SECONDS:
            return cached[1]
        catalogue = self.list_market_catalogue(market_id)
        book = self.list_market_book(market_id)
        names = {
            str(runner["selectionId"]): runner.get("runnerName", "Unknown runner")
            for runner in catalogue.get("runners", [])
        }
        observed_at = datetime.now(timezone.utc)
        prices = [
            BetfairRunnerPrice(
                market_id=str(book.get("marketId", market_id)),
                selection_id=str(runner["selectionId"]),
                runner_name=names.get(str(runner["selectionId"]), "Unknown runner"),
                status=runner.get("status", "UNKNOWN"),
                last_price_traded=(
                    Decimal(str(runner["lastPriceTraded"]))
                    if runner.get("lastPriceTraded") is not None else None
                ),
                available_to_back=_first_price(runner.get("ex", {}).get("availableToBack")),
                available_to_lay=_first_price(runner.get("ex", {}).get("availableToLay")),
                observed_at=observed_at,
                data_delayed=bool(book.get("isMarketDataDelayed", False)),
            )
            for runner in book.get("runners", [])
        ]
        _MARKET_PRICE_CACHE[market_id] = (time.monotonic(), prices)
        return prices
