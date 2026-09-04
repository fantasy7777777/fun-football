from decimal import Decimal

import pytest

from fun_football.betfair_api import BetfairExchangeClient, _first_price


def test_first_price_reads_best_offer():
    assert _first_price([{"price": 2.92, "size": 10}]) == Decimal("2.92")


def test_client_requires_both_credentials():
    with pytest.raises(Exception, match="BETFAIR_APP_KEY"):
        BetfairExchangeClient(app_key=None, session_token="token")
