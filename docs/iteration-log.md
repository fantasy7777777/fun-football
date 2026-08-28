# Iteration Log

This log records important problems, causes, solutions, and lessons learned during development.

## Iteration 0 — Repository and documentation setup

**Problem:** The local repository and GitHub repository were initially out of sync.

**Cause:** The local Git repository had an initial commit while the GitHub repository had its own initial files.

**Solution:** The remote changes were rebased into the local branch before pushing.

**Lesson:** When importing an existing GitHub repository, pull or clone it before creating competing initial commits.

## Iteration 1 — Data acquisition feasibility

**Problem:** The intended A-League data request returned no records.

**Cause:** The A-League was between seasons, and the current API catalogue did not expose the A-League sport key for the active request.

**Solution:** The API catalogue was checked and currently active competitions such as the EPL, AFL, and AFLW were tested instead.

**Lesson:** Check both competition season status and provider coverage before treating an empty response as a software failure.

## Iteration 2 — Live dashboard fallback

**Problem:** The dashboard appeared to show data, but it was synthetic sample data rather than live data.

**Cause:** The dashboard silently fell back to the sample CSV whenever the live request failed or returned no records.

**Solution:** Live mode now shows an explicit no-data or provider-error state. Sample data is only used when explicitly requested.

**Lesson:** A demonstration fallback must never look like live data.

## Iteration 3 — Local server networking

**Problem:** The browser displayed the older dashboard and live requests failed.

**Cause:** Multiple local server processes were running, and one server lacked permission to make the outbound API request.

**Solution:** Duplicate server processes were stopped and one clean server was started with network access.

**Lesson:** A local dashboard must have one clearly managed server process and a visible source status.

## Iteration 4 — Cross-platform comparison

**Problem:** The first dashboard displayed prices but did not compare the same outcome across platforms clearly.

**Cause:** Platform identity was not preserved as a first-class field in the normalised market record.

**Solution:** Platform names were retained and displayed as comparison columns for each event and outcome.

**Lesson:** Event identity, market identity, outcome identity, source identity, and observation time must remain separate.

## Iteration 5 — Betfair exchange market anomaly

**Problem:** Betfair showed a Western Bulldogs price of 110.0 while other sources showed approximately 11.0–15.0.

**Cause:** The 110.0 value came from Betfair’s `h2h_lay` exchange market, not the standard `h2h` market used by the other sources.

**Solution:** The adapter now filters to the market types explicitly requested. The default comparison uses standard `h2h` only.

**Lesson:** Prices must only be compared when the event, market type, outcome meaning, and price direction are equivalent.

## Iteration 6 — Dashboard performance

**Problem:** The dashboard could take too long to load.

**Cause:** Each page request waited synchronously for the live provider response.

**Solution:** The provider timeout was reduced and a short in-memory cache was added. The refresh action remains an explicit fresh-data request.

**Lesson:** Live data needs timeout handling, caching, and clear freshness indicators.

## Entry format for future iterations

For each significant issue, record:

- **Problem** — what was observed
- **Cause** — why it happened
- **Solution** — what changed
- **Lesson** — what should guide future work
