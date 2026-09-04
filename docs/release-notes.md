# Release Notes

## Version 0.2.0 — Presentation-ready dashboard

### Added

- Live read-only market retrieval through The Odds API.
- Cross-source comparison for the same event, market, and outcome.
- Competition selection for Premier League, A-League, AFL, and AFLW where provider data is available.
- Market selection for Win/Draw/Loss and Over/Under 2.5 goals.
- Explicit source states for live data, unavailable data, no current data, and synthetic demo data.
- Visible data-quality checks for event counts, quote counts, missing team names, invalid prices, and duplicate records.
- Premier League scenario-analysis page with selectable, removable, and manually addable teams.
- Documentation for API security, source limitations, data provenance, and responsible use.
- Read-only Betfair connector for joining AFL market runner names with delayed exchange price observations.
- Dedicated AFL Premiers 2026 dashboard page using the configured Betfair read-only connector.
- Editable target-payout calculations on the AFL championship page, including required amount and theoretical net difference per priced team.
- Multi-team selection controls with combined theoretical outlay, target payout, and net-difference calculations.
- Multi-source championship layout with Betfair delayed observations and a clearly labelled synthetic manual research sample.

### Important limitations

- The dashboard compares published observations; it does not predict outcomes or provide recommendations.
- The current provider does not expose Premier League championship outright prices in the active catalogue.
- Scenario-analysis prices are editable theoretical values, not live championship prices.
- Provider coverage varies by competition, region, market, bookmaker, time, account plan, and quota.
- A successful provider request does not guarantee that every source offers the same market or line.
- Betfair integration is read-only and currently requires local credentials; it does not place orders or access account balances.
- The AFL championship page currently targets the researched `Premiers 2026` market ID and should be updated when a new season market is selected.

### Security notes

- API credentials remain local and are excluded through `.gitignore`.
- No account passwords, session tokens, cookies, or transaction credentials belong in the repository.
- Review `docs/security-model.md` and `docs/api-integration.md` before adding another data source.
