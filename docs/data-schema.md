# Common Data Schema

The first implementation uses three linked records:

| Record | Purpose | Key fields |
|---|---|---|
| `Event` | A scheduled match | competition, teams, start time, source identity |
| `Market` | A named market for an event | market type, event link, live/pre-match flag |
| `PriceQuote` | One observed outcome price | outcome, decimal price, timestamp, source |

Each observation must retain its source and timestamp. Source-specific identifiers are kept alongside the normalised identifiers so that records can be traced back and corrected.

Comparisons must use the same market type. For example, standard `h2h` prices must not be mixed with exchange-specific `h2h_lay` prices. The API adapter filters to the market types requested by the caller.

The Python implementation is in `src/fun_football/schema.py`. It currently validates required text fields, timezone-aware timestamps, distinct teams, and prices greater than 1.
