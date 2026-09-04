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

## Iteration 7 — Source visibility and data-quality checks

**Problem:** A presentation viewer could not quickly distinguish the active source from sample data or see whether the records had basic integrity issues.

**Cause:** Source state was shown as a status sentence, but the dashboard did not provide a compact quality summary for events, quotes, invalid prices, missing teams, or duplicate quote records.

**Solution:** The dashboard now labels the source section explicitly and displays data-quality check counts for every response. Warnings are shown when invalid or duplicate records are detected.

**Lesson:** A data demonstration should make both provenance and basic validation visible at the point where results are viewed.

## Iteration 8 — Additional football market

**Problem:** The dashboard only demonstrated Win/Draw/Loss comparisons.

**Cause:** The market selection was fixed to `h2h` in both the dashboard and API request.

**Solution:** Added a market selector for `Over / Under 2.5 goals`. The selected market is requested from the provider, displayed in each event card, and sorted consistently as Over then Under. Sample mode filters to the selected market and therefore does not present Win/Draw/Loss records as totals.

**Lesson:** Each comparison must request and display one explicit market type; outcomes from different markets must never be mixed.

## Iteration 9 — Betfair read-only market connector

**Problem:** The provider used for the main dashboard did not expose Premier League or Australian championship outright prices, while Betfair showed an AFL `Premiers 2026` market in its exchange API.

**Cause:** Betfair uses an authenticated JSON-RPC API and separates runner metadata from dynamic market-book prices. The project had no adapter for joining those two responses.

**Solution:** Added a read-only Betfair adapter that retrieves market catalogue runner names, retrieves market-book observations, and joins selection IDs to team names and prices. The adapter requests delayed/development-compatible price data and contains no order-placement or account-operation methods.

**Lesson:** A new source should have a narrow, provider-specific adapter, explicit credential boundaries, and a normalised output before it reaches analysis or presentation code.

## Iteration 10 — AFL championship dashboard

**Problem:** Betfair championship data could be retrieved by code but was not visible in the presentation dashboard.

**Cause:** The connector and the existing theoretical scenario page were separate, and the scenario page intentionally used editable values rather than live championship prices.

**Solution:** Added a dedicated AFL Premiers 2026 page that joins Betfair runner names to delayed exchange observations and displays status, last-traded prices, available offers, and data-source limitations.

**Lesson:** Live or delayed observations should have a separate presentation surface from theoretical calculations, with provenance and delay status visible beside the data.

## Iteration 11 — Championship scenario calculations

**Problem:** The championship page displayed Betfair prices but did not show the corresponding theoretical amount and target payout calculation.

**Cause:** The calculation existed only on the separate scenario page, while the championship page presented observations as a read-only table.

**Solution:** Added an editable target gross payout and per-team calculations for required amount, gross payout, and theoretical net difference based on each delayed last-traded price.

**Lesson:** Calculations derived from live or delayed observations must remain clearly labelled as theoretical and must identify the input price and assumptions.

## Iteration 12 — Multi-team championship scenarios

**Problem:** The championship page calculated each team independently and did not allow a user to model a selected group of teams together.

**Cause:** The page had per-team calculation columns but no selection state or combined totals.

**Solution:** Added checkboxes, select-all and clear-selection controls, and combined results for selected teams. The page now shows combined theoretical outlay, target gross payout if one selected team wins, and theoretical net difference.

**Lesson:** A multi-outcome calculation must show the combined assumptions and result, while keeping the user’s selection explicit and avoiding automatic recommendations.

## Iteration 13 — Flexible team selection

**Problem:** The first combined-scenario interface made bulk selection controls too prominent, making the interaction feel all-or-nothing.

**Cause:** Select-all and clear-all actions were placed alongside the primary calculation controls.

**Solution:** Removed the bulk buttons and made individual team checkboxes the primary interaction. Selected rows are highlighted, and the combined figures update for any chosen subset.

**Lesson:** User-selected combinations should be explicit at row level; convenience actions must not obscure flexible selection.

## Iteration 14 — Multi-source championship layout

**Problem:** The AFL championship page displayed only Betfair observations, making it difficult to demonstrate how another permitted source would be compared.

**Cause:** The page was coupled to the Betfair runner-price result and had no source-aware calculation selector.

**Solution:** Added a clearly labelled manual research sample source, separate source columns, and a calculation-source selector. The manual values are synthetic demonstration content and are not presented as live data.

**Lesson:** Multi-source support must preserve provenance and distinguish live, delayed, and synthetic records; a demonstration source must never be mistaken for a provider feed.

## Iteration 15 — Betfair response caching

**Problem:** Reopening the AFL championship page repeatedly waited for the Betfair catalogue and market-book requests each time.

**Cause:** The page performed two authenticated read-only provider requests on every request, even when the market had not materially changed.

**Solution:** Added a 60-second in-memory cache for joined Betfair market-price results. Normal reloads reuse the recent result; an explicit `refresh=1` request bypasses the cache.

**Lesson:** Short-lived caching improves presentation responsiveness while preserving an explicit path for the user to request fresh observations.

## Iteration 16 — Unpriced-runner selection fallback

**Problem:** The Betfair market could return runner names without last-traded prices, which left every Betfair-based calculator checkbox disabled.

**Cause:** The calculator selected Betfair by default even when that snapshot contained no usable Betfair prices.

**Solution:** The page now detects the number of usable Betfair prices and defaults to the clearly labelled synthetic manual sample when the count is zero. Users can still select individual teams and switch sources when Betfair prices become available.

**Lesson:** A source may be structurally available but not numerically usable; the interface must distinguish those states and preserve a usable, honest demonstration path.

## Iteration 17 — Preserve unavailable runners

**Problem:** When Betfair was unavailable and the page used the manual demonstration source, only the nine manually priced teams appeared; previously observed eliminated teams were not visible.

**Cause:** The display list was built only from the current Betfair response and manual sample rows.

**Solution:** The page now retains the known 18-team AFL list and marks teams absent from the current response as `NOT RETURNED`. Such rows remain visible but cannot be selected without a usable price.

**Lesson:** Missing or inactive data should be represented explicitly rather than silently removing entities from a comparison view.

## Entry format for future iterations

For each significant issue, record:

- **Problem** — what was observed
- **Cause** — why it happened
- **Solution** — what changed
- **Lesson** — what should guide future work
