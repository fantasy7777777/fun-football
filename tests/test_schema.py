from datetime import datetime, timezone
from decimal import Decimal

import pytest

from fun_football.schema import Event, Market, PriceQuote


def test_event_normalises_time_to_utc():
    event = Event(
        event_id="event-1",
        sport="football",
        country="Australia",
        competition="A-League",
        home_team="Team A",
        away_team="Team B",
        start_time=datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc),
        source="example-feed",
    )
    assert event.start_time.tzinfo == timezone.utc


def test_market_and_quote_link_to_event():
    market = Market("market-1", "event-1", "1X2", "example-feed")
    quote = PriceQuote(
        "quote-1", market.market_id, "home", Decimal("2.10"),
        datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc), "example-feed"
    )
    assert quote.market_id == market.market_id


def test_quote_rejects_invalid_price():
    with pytest.raises(ValueError, match="greater than 1"):
        PriceQuote(
            "quote-1", "market-1", "home", Decimal("1.00"),
            datetime.now(timezone.utc), "example-feed"
        )
