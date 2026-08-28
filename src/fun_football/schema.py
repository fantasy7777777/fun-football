"""Source-independent schema for football market data.

The schema stores observations and provenance. It does not make predictions,
recommendations, or claims about financial outcomes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


def _require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _require_utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Event:
    """A scheduled football event from a competition."""

    event_id: str
    sport: str
    country: str
    competition: str
    home_team: str
    away_team: str
    start_time: datetime
    source: str
    source_event_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value, name in ((self.event_id, "event_id"), (self.sport, "sport"),
                            (self.country, "country"), (self.competition, "competition"),
                            (self.home_team, "home_team"), (self.away_team, "away_team"),
                            (self.source, "source")):
            _require_text(value, name)
        if self.home_team.casefold() == self.away_team.casefold():
            raise ValueError("home_team and away_team must be different")
        object.__setattr__(self, "start_time", _require_utc(self.start_time, "start_time"))


@dataclass(frozen=True)
class Market:
    """A named market offered for an event, such as 1X2."""

    market_id: str
    event_id: str
    market_type: str
    source: str
    source_market_id: str | None = None
    is_live: bool = False
    source_name: str | None = None

    def __post_init__(self) -> None:
        for value, name in ((self.market_id, "market_id"), (self.event_id, "event_id"),
                            (self.market_type, "market_type"), (self.source, "source")):
            _require_text(value, name)


@dataclass(frozen=True)
class PriceQuote:
    """One timestamped published price observation."""

    quote_id: str
    market_id: str
    outcome: str
    price: Decimal
    observed_at: datetime
    source: str
    currency: str = "AUD"
    source_url: str | None = None

    def __post_init__(self) -> None:
        for value, name in ((self.quote_id, "quote_id"), (self.market_id, "market_id"),
                            (self.outcome, "outcome"), (self.source, "source"),
                            (self.currency, "currency")):
            _require_text(value, name)
        if self.price <= 1:
            raise ValueError("price must be greater than 1")
        object.__setattr__(self, "observed_at", _require_utc(self.observed_at, "observed_at"))
