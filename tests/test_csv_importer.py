from pathlib import Path

from fun_football.csv_importer import load_market_csv


def test_example_csv_loads_three_quotes():
    records = load_market_csv(Path("data/examples/market_quotes.csv"))
    assert len(records) == 3
    assert records[0][0].competition == "A-League"
    assert records[0][2].currency == "AUD"
