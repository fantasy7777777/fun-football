# Data Sources

This document records where project data comes from and what use is permitted.

For each source, record:

- Provider name and URL
- Data type and fields used
- Collection method
- Access date and timezone
- Licence or terms reviewed
- Whether redistribution is permitted
- Known limitations and data-quality concerns

Do not store credentials or restricted raw responses in the repository. Keep local secrets in environment variables and keep local datasets under the ignored `data/` folders unless their licence clearly permits publication.

## Initial source assessment

The preferred path is an official API or a data provider that grants explicit API access and documents permitted use.

- Direct Bet365 or Sportsbet page collection should not be assumed to be permitted. Use only an official developer interface or written permission; do not bypass authentication, rate limits, or technical controls.
- The Odds API documents an Australia region and A-League coverage. It is a possible research source, but its terms control retention, redistribution, attribution, and use of the data.
- API-Football documents football odds endpoints, but its terms state that users are responsible for obtaining any permissions required to publish or use competition data.
- Betfair provides an official API, but it includes account and transaction capabilities. Any future use should be restricted to the minimum read-only data access needed for the demo and reviewed against its current terms.

No source should be labelled “legal” solely because its data is visible on a website. Record the provider, access method, plan, terms reviewed, and publication permissions before integration.
