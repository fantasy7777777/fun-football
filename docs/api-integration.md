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
