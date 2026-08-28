# Feasibility Assessment

## Conclusion

Fun Football is feasible as a small research and software demonstration. The technically difficult part is not normalising prices; it is obtaining a stable, permitted, sufficiently complete data feed and preserving source provenance.

## Acquisition options

| Option | Feasibility | Recommendation |
|---|---|---|
| Licensed API or feed | High if Australian football coverage is included in the plan | Preferred first choice |
| Direct website automation | Technically possible, permission uncertain | Do not use without explicit permission and a terms review |
| Manual CSV entry | High for a small demonstration | Use as the first fallback and test fixture source |
| Synthetic/mock data | Very high | Use for development before live credentials |

## API-first decision

The first live-data experiment should use a provider that expressly grants API access. The provider must be checked for Australian football coverage, update frequency, historical access, rate limits, retention, attribution, and redistribution rights.

The Odds API documents an Australia bookmaker region and A-League coverage. Its terms allow analytical tools but restrict reselling or redistributing the data as a standalone data product. This makes it a plausible research input, not automatically a licence to publish the raw feed.

API-Football documents pre-match odds endpoints, but its terms place responsibility on the user to obtain permissions required for use or publication. Coverage and permissions should be confirmed before implementation.

## Scraping decision

“Visible on a website” does not mean “permitted to automate, copy, store, or redistribute.” Bet365’s published terms specifically address automated copying or extraction of service data, including odds. I did not identify a public official developer API for Sportsbet in this assessment. Therefore, direct scraping of either provider is not an approved fallback for this project unless the provider gives written permission or publishes terms that clearly permit the exact use.

If a permitted web source is ever used, keep collection low-volume, respect robots and rate limits, do not bypass controls or authentication, retain only the minimum data needed, and document the permission and terms reviewed.

## Manual and mock fallback

Manual entry is suitable for the first end-to-end demonstration. A small CSV can exercise event matching, validation, timestamp handling, source provenance, and comparison logic without live credentials. Mock data should be used in automated tests and development.

## Recommended sequence

1. Complete the common schema and validation tests.
2. Build a CSV importer using manually entered or synthetic records.
3. Evaluate one licensed API against the source checklist.
4. Add a read-only API adapter only after its terms and plan are confirmed.
5. Keep direct bookmaker scraping out of scope unless written permission is obtained.

## Scope guardrails

The system remains a data-analysis experiment. It will not log into external accounts, place transactions, provide personalised recommendations, or present theoretical results as guaranteed outcomes.
