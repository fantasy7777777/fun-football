# Development Notes

Use this document for decisions made during implementation, including rejected alternatives, assumptions, and follow-up work.

Initial decision: start with a small, source-independent data model so additional Australian competitions or data providers can be added without rewriting the analysis layer.

## Source visibility and validation

The dashboard keeps source status separate from data-quality status. Source status identifies whether the page uses live API data, explicitly requested sample data, or an unavailable provider. Quality checks count discovered events and quotes and flag missing team names, prices at or below 1.00, and duplicate event/market/source/outcome records. These checks are diagnostic only; they do not modify or silently discard provider records.

The scenario analysis page uses the live API only to discover current Premier League fixture team names. Its editable prices remain clearly theoretical because the current provider catalogue does not expose Premier League outright prices.

## Market selection

The market monitor supports standard `h2h` (Win / Draw / Loss) and `totals` (Over / Under 2.5 goals) requests. The selected market is passed through to the API client and retained in the rendered event metadata. The dashboard does not combine outcomes from different market types. Additional markets should be added only after confirming provider coverage and defining their outcome and line normalisation rules.
