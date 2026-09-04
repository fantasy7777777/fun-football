# API Integration

The initial live-data adapter targets The Odds API using read-only requests.

## Local setup

Create `.env` in the repository root:

```text
ODDS_API_KEY=your_key_here
```

The key is ignored by Git and must never be committed, logged, or shared.

The default request targets the documented A-League sport key, the Australian bookmaker region, and the head-to-head market. Provider coverage, quotas, freshness, retention, attribution, and redistribution permissions must be checked against the active account plan and terms before using the data beyond local testing.

The adapter does not log in to bookmaker accounts, place transactions, or provide recommendations. It only reads the provider API and converts responses into the common schema.

The default comparison requests the standard `h2h` market only. Exchange-specific markets such as `h2h_lay` are excluded because their prices are not directly comparable with ordinary win-price observations.

## API security boundary

The API key is loaded locally by the Python adapter from `ODDS_API_KEY`; it is never sent to the browser and is never included in rendered HTML. The local dashboard acts as a small server-side proxy for read-only data retrieval. Requests have a timeout and the adapter caches recent responses to reduce repeated calls.

For future providers such as Betfair, credentials must remain server-side. Session tokens, application keys, cookies, and account credentials must not be committed or displayed. The intended integration boundary is market discovery and price retrieval only; order placement, account balances, and other transaction operations are out of scope.

Before using a source beyond local demonstration, confirm its authentication requirements, permitted use, rate limits, data retention rules, attribution requirements, and redistribution licence. Public visibility of a webpage or endpoint does not by itself grant permission to collect or republish its data.

## Betfair read-only connector

`src/fun_football/betfair_api.py` provides a small JSON-RPC client for Betfair's Betting API. It supports `listMarketCatalogue` and `listMarketBook`, then joins runner names from the catalogue to delayed/live price observations from the market book. It intentionally contains no order-placement or account-operation methods.

Configure it locally with the delayed development key and current session token:

```text
BETFAIR_APP_KEY=your_delayed_application_key
BETFAIR_SESSION_TOKEN=your_session_token
```

The connector requests `EX_BEST_OFFERS` and `SP_TRADED`. A missing best offer is represented as `None`; it must not be replaced with a fabricated price. Betfair's delayed key may return delayed data and has provider-specific limits, so the dashboard must label the observation status and timestamp accurately.

Joined Betfair market-price results are cached in memory for 60 seconds to avoid repeating the catalogue and market-book calls during presentation reloads. The cache is process-local, is not written to disk, and can be bypassed with the dashboard's explicit refresh request.

The AFL championship page also includes a local synthetic sample source to exercise the multi-source layout. It is not a second live provider and must not be described as one. Replacing it with another source requires permission, credentials, coverage confirmation, and an adapter that preserves market, outcome, timestamp, and price-direction semantics.
