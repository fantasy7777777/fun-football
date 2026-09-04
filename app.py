"""Small local presentation dashboard for Fun Football."""

from collections import defaultdict
import csv
from decimal import Decimal
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fun_football.csv_importer import load_market_csv
from fun_football.betfair_api import BetfairApiError, BetfairExchangeClient
from fun_football.odds_api import OddsApiError, TheOddsApiClient


SPORTS = {
    "soccer_epl": "Premier League",
    "soccer_australia_aleague": "A-League",
    "aussierules_afl": "AFL",
    "aussierules_aflw": "AFLW",
}
MARKETS = {
    "h2h": "Win / Draw / Loss",
    "totals": "Over / Under 2.5 goals",
}
AFL_PREMIERS_MARKET_ID = "1.248306161"
AFL_PREMIERS_KNOWN_TEAMS = {
    "Adelaide", "Brisbane", "Carlton", "Collingwood", "Essendon", "Fremantle",
    "Geelong", "Gold Coast", "GWS", "Hawthorn", "Melbourne", "North Melbourne",
    "Port Adelaide", "Richmond", "St Kilda", "Sydney", "West Coast", "Western Bulldogs",
}


def _format_time(value) -> str:
    return value.strftime("%d %b %Y, %H:%M UTC")


def _live_rows(sport_key: str, markets: str = "h2h", force_refresh: bool = False):
    return TheOddsApiClient().get_odds(
        sport_key=sport_key, regions="au", markets=markets, force_refresh=force_refresh
    )


def _sample_rows():
    return load_market_csv(Path("data/examples/market_quotes.csv"))


def _quality_checks(rows):
    """Return small, presentation-friendly checks for normalised records."""
    event_ids = set()
    missing_event_fields = 0
    invalid_prices = 0
    quote_keys = set()
    duplicate_quotes = 0
    for event, market, quote in rows:
        event_ids.add(event.event_id)
        if not event.home_team.strip() or not event.away_team.strip():
            missing_event_fields += 1
        if quote.price <= 1:
            invalid_prices += 1
        quote_key = (event.event_id, market.market_type, market.source_name, quote.outcome)
        if quote_key in quote_keys:
            duplicate_quotes += 1
        quote_keys.add(quote_key)
    return [
        ("Events discovered", len(event_ids), "ok"),
        ("Quotes received", len(rows), "ok"),
        ("Missing team names", missing_event_fields, "warning" if missing_event_fields else "ok"),
        ("Invalid prices (≤ 1.00)", invalid_prices, "warning" if invalid_prices else "ok"),
        ("Duplicate quote records", duplicate_quotes, "warning" if duplicate_quotes else "ok"),
    ]


def _scenario_dashboard(team_names=None, team_source="Example team list") -> str:
    initial_teams = [[name, 6.00] for name in (team_names or [
        "Arsenal", "Manchester United", "Tottenham Hotspur", "Chelsea",
        "Liverpool", "Manchester City",
    ])]
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fun Football — Premier League Scenario Analysis</title>
<style>
  :root { color-scheme: dark; --bg:#10131a; --panel:#191e28; --line:#303847; --text:#f3f5f7; --muted:#aab3c1; --accent:#64d6a0; --warn:#f4c56d; }
  * { box-sizing:border-box; } body { margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,sans-serif; }
  main { max-width:820px; margin:0 auto; padding:42px 22px 64px; } h1 { margin:0; font-size:32px; letter-spacing:-.03em; } h1 small { color:var(--accent); font-size:13px; display:block; letter-spacing:.12em; text-transform:uppercase; margin-bottom:8px; }
  p { color:var(--muted); } .panel { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:20px; margin-top:22px; } .rows { display:grid; gap:10px; } .row { display:grid; grid-template-columns:1fr 160px; gap:12px; align-items:center; } label { color:var(--muted); font-size:13px; } input { width:100%; background:var(--bg); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px; font:inherit; }
  .team-tools { display:flex; align-items:center; flex-wrap:wrap; gap:8px; margin:22px 0 12px; } .team-tools strong { margin-right:auto; } .team-tools button, .custom button, .team-option button { background:var(--bg); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:8px 10px; font:inherit; cursor:pointer; } .team-options { display:grid; grid-template-columns:repeat(2,1fr); gap:8px; } .team-option { display:grid; grid-template-columns:auto 1fr auto auto; gap:8px; align-items:center; background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:10px; } .team-option input { width:auto; } .team-option .price { width:100px; } .team-option button { color:var(--warn); padding:6px 8px; } .custom { display:grid; grid-template-columns:1fr auto; gap:8px; align-items:end; margin-top:16px; } .custom label { grid-column:1 / -1; } .custom select { width:100%; background:var(--bg); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px; font:inherit; } .results { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-top:22px; } .result { background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:14px; } .result b { display:block; color:var(--accent); font-size:22px; } .result span { color:var(--muted); font-size:12px; } .positive { color:var(--accent); } .negative { color:var(--warn); } table { width:100%; border-collapse:collapse; margin-top:16px; } th,td { text-align:left; padding:8px 6px 8px 0; border-bottom:1px solid var(--line); } th { color:var(--muted); font-weight:500; } .note { font-size:12px; margin-top:18px; } a { color:var(--accent); }
  @media(max-width:600px) { main { padding:28px 14px; } .row { grid-template-columns:1fr; gap:4px; } .results { grid-template-columns:1fr; } }
</style></head><body><main>
<h1><small>Fun Football · Premier League</small>Scenario analysis</h1>
<p>Explore an equal-target-payout calculation using Premier League team selections. __TEAM_SOURCE__ This is a theoretical research tool, not a recommendation or transaction interface.</p>
<section class="panel"><div class="row"><label for="target">Target gross payout</label><input id="target" type="number" min="0.01" step="0.01" value="100"></div>
<div class="team-tools"><strong>Choose teams</strong><button type="button" id="selectAll">Select all</button><button type="button" id="clearAll">Clear all</button></div>
<div id="teamOptions" class="team-options"></div>
<div class="custom"><label for="teamPicker">Add another team</label><select id="teamPicker"><option value="">Select a team…</option><option value="Arsenal">Arsenal</option><option value="Manchester United">Manchester United</option><option value="Tottenham Hotspur">Tottenham Hotspur</option><option value="Chelsea">Chelsea</option><option value="Liverpool">Liverpool</option><option value="Manchester City">Manchester City</option><option value="Aston Villa">Aston Villa</option><option value="Brighton &amp; Hove Albion">Brighton &amp; Hove Albion</option><option value="Everton">Everton</option><option value="Fulham">Fulham</option><option value="Leeds United">Leeds United</option><option value="Newcastle United">Newcastle United</option><option value="West Ham United">West Ham United</option><option value="Other">Other…</option></select><button type="button" id="addTeam">Add team</button></div>
<div class="results" aria-live="polite"><div class="result"><b id="total">—</b><span>Total theoretical outlay</span></div><div class="result"><b id="coverage">—</b><span>Implied coverage ratio</span></div><div class="result"><b id="net">—</b><span>Theoretical net difference</span></div></div>
<table><thead><tr><th>Selected team</th><th>Price</th><th>Required amount</th></tr></thead><tbody id="breakdown"></tbody></table>
<p class="note">The calculation assumes mutually exclusive outcomes, identical target payouts, unchanged prices, and successful settlement. It excludes fees, limits, delays, voids, and the possibility that none of the selected outcomes occurs.</p></section>
<p><a href="/?sport_key=soccer_epl">← Return to market monitor</a></p>
<script>
const initialTeams = __INITIAL_TEAMS__;
const money = value => Number.isFinite(value) ? value.toFixed(2) : '—';
function addTeam(name, price, checked = true) {
  const wrapper = document.createElement('div'); wrapper.className = 'team-option'; wrapper.dataset.team = name;
  wrapper.innerHTML = '<input type="checkbox" class="team-check" ' + (checked ? 'checked' : '') + '><span>' + name + '</span><input class="price" type="number" min="1.01" step="0.01" value="' + price + '" aria-label="Price for ' + name + '"><button type="button" class="remove-team" aria-label="Remove ' + name + '">Remove</button>';
  document.getElementById('teamOptions').appendChild(wrapper);
  wrapper.querySelectorAll('input').forEach(input => input.addEventListener('input', calculate));
  wrapper.querySelector('.team-check').addEventListener('change', calculate); calculate();
  wrapper.querySelector('.remove-team').addEventListener('click', () => { wrapper.remove(); calculate(); });
}
function calculate() {
  const target = Number(document.getElementById('target').value);
  const rows = [...document.querySelectorAll('.team-option')].filter(row => row.querySelector('.team-check').checked).map(row => ({ label: row.dataset.team, price: Number(row.querySelector('.price').value) })).filter(row => row.price > 1);
  const amounts = rows.map(row => ({ ...row, required: target / row.price }));
  const total = amounts.reduce((sum, row) => sum + row.required, 0);
  const coverage = amounts.reduce((sum, row) => sum + 1 / row.price, 0);
  const net = target - total;
  document.getElementById('total').textContent = money(total);
  document.getElementById('coverage').textContent = (coverage * 100).toFixed(2) + '%';
  const netElement = document.getElementById('net'); netElement.textContent = money(net); netElement.className = net >= 0 ? 'positive' : 'negative';
  document.getElementById('breakdown').innerHTML = amounts.map(row => '<tr><td>' + row.label + '</td><td>' + money(row.price) + '</td><td>' + money(row.required) + '</td></tr>').join('');
}
initialTeams.forEach(team => addTeam(team[0], team[1]));
document.getElementById('target').addEventListener('input', calculate);
document.getElementById('selectAll').addEventListener('click', () => { document.querySelectorAll('.team-check').forEach(input => input.checked = true); calculate(); });
document.getElementById('clearAll').addEventListener('click', () => { document.querySelectorAll('.team-check').forEach(input => input.checked = false); calculate(); });
document.getElementById('addTeam').addEventListener('click', () => { const picker = document.getElementById('teamPicker'); const name = picker.value; if (name && name !== 'Other') { if (![...document.querySelectorAll('.team-option')].some(row => row.dataset.team === name)) addTeam(name, 6.00); picker.value = ''; } else if (name === 'Other') { const custom = window.prompt('Enter a team name'); if (custom && custom.trim()) { addTeam(custom.trim(), 6.00); picker.value = ''; } } });
calculate();
</script></main></body></html>"""
    return page.replace("__INITIAL_TEAMS__", json.dumps(initial_teams)).replace(
        "__TEAM_SOURCE__", escape(team_source)
    )


def _afl_premiers_dashboard(force_refresh: bool = False) -> str:
    """Render the current read-only Betfair AFL championship market."""
    error = ""
    betfair_response_available = False
    try:
        rows = BetfairExchangeClient().get_market_prices(AFL_PREMIERS_MARKET_ID, force_refresh=force_refresh)
        betfair_response_available = True
        market_status = "Betfair delayed exchange data"
        market_detail = "Premiers 2026 · Market observations only · No transactions provided"
    except BetfairApiError as exc:
        rows = []
        market_status = "Betfair data unavailable"
        market_detail = "Configure a delayed application key and current session token in .env"
        error = str(exc)

    manual_prices = {}
    manual_path = Path("data/examples/afl_premiers_manual_sample.csv")
    with manual_path.open(newline="", encoding="utf-8") as sample_file:
        for record in csv.DictReader(sample_file):
            manual_prices[record["team"]] = Decimal(record["price"])
    betfair_by_team = {row.runner_name: row for row in rows}
    team_names = sorted(set(betfair_by_team) | set(manual_prices) | AFL_PREMIERS_KNOWN_TEAMS)
    betfair_price_count = sum(
        row.last_price_traded is not None for row in betfair_by_team.values()
    )
    default_price_source = "betfair" if betfair_price_count else "manual"
    source_note = (
        "Betfair prices are available for calculation."
        if betfair_price_count
        else "Betfair returned no usable last-traded prices for this snapshot, so the calculator starts with the synthetic manual sample."
    )

    def price(value):
        return f"{value:.2f}" if value is not None else "—"

    def team_status(team):
        return (
            betfair_by_team[team].status
            if team in betfair_by_team
            else ("NOT RETURNED" if betfair_response_available else "NO API RESPONSE")
        )

    active_teams = sorted(
        (team for team in team_names if team_status(team) == "ACTIVE"), key=str.casefold
    )
    other_teams = sorted(
        (team for team in team_names if team_status(team) != "ACTIVE"), key=str.casefold
    )

    def team_row(team):
        return (
            f'<tr data-betfair="{betfair_by_team[team].last_price_traded if team in betfair_by_team and betfair_by_team[team].last_price_traded is not None else ""}" data-manual="{manual_prices.get(team, "")}">'
            f'<td><input class="team-select" type="checkbox" aria-label="Select {escape(team)}"></td>'
            f"<td>{escape(team)}</td><td>{escape(team_status(team))}</td>"
            f"<td>{price(betfair_by_team[team].last_price_traded if team in betfair_by_team else None)}</td>"
            f"<td>{price(manual_prices.get(team))}</td><td class=\"selected-price\">—</td><td class=\"required\">—</td>"
            f"<td class=\"gross\">—</td><td class=\"net\">—</td></tr>"
        )

    groups = []
    if active_teams:
        groups.append('<tr class="group-heading"><th colspan="9">Active teams</th></tr>')
        groups.extend(team_row(team) for team in active_teams)
    if other_teams:
        groups.append('<tr class="group-heading"><th colspan="9">Inactive or unavailable teams</th></tr>')
        groups.extend(team_row(team) for team in other_teams)
    rows_html = "".join(groups) or '<tr><td colspan="9" class="empty">No market observations available.</td></tr>'
    error_html = f'<p class="error">{escape(error)}</p>' if error else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fun Football — AFL Premiers 2026</title>
<style>
  :root {{ color-scheme: dark; --bg:#10131a; --panel:#191e28; --line:#303847; --text:#f3f5f7; --muted:#aab3c1; --accent:#64d6a0; --warn:#f4c56d; }}
  * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,sans-serif; }}
  main {{ width:100%; max-width:none; margin:0; padding:42px 32px 64px; }} h1 {{ margin:0; font-size:32px; letter-spacing:-.03em; }} h1 small {{ color:var(--accent); font-size:13px; display:block; letter-spacing:.12em; text-transform:uppercase; margin-bottom:8px; }}
  p {{ color:var(--muted); }} .status {{ border:1px solid var(--line); background:var(--panel); border-radius:12px; padding:16px; margin:22px 0; }} .status small {{ display:block; color:var(--muted); letter-spacing:.1em; font-size:11px; }} .status strong {{ color:var(--accent); }} .status p {{ margin:3px 0 0; }} .error {{ color:var(--warn); }}
  .summary {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:22px; }} .summary div {{ min-width:130px; background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px 14px; }} .summary b {{ display:block; color:var(--accent); font-size:20px; }} .summary span {{ color:var(--muted); font-size:12px; }}
  .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:18px; overflow:auto; }} .calculator {{ display:flex; align-items:end; gap:10px; flex-wrap:wrap; margin-bottom:14px; }} .calculator label {{ display:grid; gap:5px; color:var(--muted); font-size:12px; }} .calculator input, .calculator select {{ width:190px; background:var(--bg); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:9px; font:inherit; }} .selection-summary {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; }} .selection-summary div {{ min-width:145px; background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:10px; }} .selection-summary b {{ display:block; color:var(--accent); font-size:18px; }} .selection-summary span {{ color:var(--muted); font-size:11px; }} table {{ width:100%; min-width:1120px; table-layout:fixed; border-collapse:collapse; }} th,td {{ text-align:left; padding:9px 14px 9px 0; border-bottom:1px solid var(--line); white-space:nowrap; }} th {{ color:var(--muted); font-weight:500; }} th:nth-child(1), td:nth-child(1) {{ width:64px; }} th:nth-child(2), td:nth-child(2) {{ width:155px; }} th:nth-child(3), td:nth-child(3) {{ width:120px; }} th:nth-child(4), td:nth-child(4) {{ width:170px; }} th:nth-child(5), td:nth-child(5) {{ width:140px; }} th:nth-child(6), td:nth-child(6) {{ width:140px; }} th:nth-child(7), td:nth-child(7) {{ width:145px; }} th:nth-child(8), td:nth-child(8) {{ width:140px; }} th:nth-child(9), td:nth-child(9) {{ width:140px; }} .group-heading th {{ padding-top:15px; color:var(--accent); background:rgba(100,214,160,.06); border-top:2px solid var(--line); }} td:not(:first-child) {{ color:var(--accent); }} tbody tr.selected {{ background:rgba(100,214,160,.10); }} .team-select {{ width:18px; height:18px; accent-color:var(--accent); cursor:pointer; }} .net.positive {{ color:var(--accent); }} .net.negative {{ color:var(--warn); }} .empty {{ color:var(--muted); }} .note {{ font-size:12px; margin-top:18px; }} a {{ color:var(--accent); }}
  @media(max-width:600px) {{ main {{ padding:28px 14px; }} h1 {{ font-size:27px; }} }}
</style></head><body><main>
<h1><small>Fun Football · Australian Rules</small>AFL Premiers 2026</h1>
<p>Read-only championship market view using the Betfair exchange market discovered during the project research.</p>
<section class="status" aria-live="polite"><small>DATA SOURCE</small><strong>{escape(market_status)}</strong><p>{escape(market_detail)}</p>{error_html}</section>
<section class="summary"><div><b>{len(rows)}</b><span>runner(s)</span></div><div><b>{sum(row.status == "ACTIVE" for row in rows)}</b><span>active runner(s)</span></div><div><b>{sum(row.last_price_traded is not None for row in rows)}</b><span>last-traded prices</span></div></section>
<section class="panel"><div class="calculator"><label for="target">Target theoretical gross payout<input id="target" type="number" min="0.01" step="0.01" value="100"></label><label for="priceSource">Bet rate source<select id="priceSource"><option value="betfair"{" selected" if default_price_source == "betfair" else ""}>Betfair delayed last traded</option><option value="manual"{" selected" if default_price_source == "manual" else ""}>Manual research sample</option></select></label><span>{escape(source_note)}</span></div><div class="selection-summary" aria-live="polite"><div><b id="selectedCount">0</b><span>selected team(s)</span></div><div><b id="selectedOutlay">—</b><span>combined theoretical outlay</span></div><div><b id="selectedGross">—</b><span>target gross payout if one wins</span></div><div><b id="selectedNet">—</b><span>theoretical net difference</span></div></div><table><caption>Betfair observations and manual demonstration values; values may be delayed or synthetic</caption><thead><tr><th>Select</th><th>Team</th><th>Status</th><th>Betfair last traded</th><th>Manual sample</th><th>Selected bet rate</th><th>Required amount</th><th>Gross payout</th><th>Net difference</th></tr></thead><tbody>{rows_html}</tbody></table><p class="note">Select any combination of teams to model a combined, mutually exclusive championship scenario. The manual research sample is synthetic demonstration content and is not a second live source. Required amount and net difference are illustrative calculations. They are not predictions, recommendations, guarantees, or instructions to transact.</p></section>
<p><a href="/?view=scenario">← Open theoretical scenario analysis</a> · <a href="/?sport_key=aussierules_afl">Open AFL match monitor</a></p>
<script>
function updateCalculations() {{
  const target = Number(document.getElementById('target').value);
  let selectedCount = 0, selectedOutlay = 0;
  document.querySelectorAll('tbody tr[data-betfair], tbody tr[data-manual]').forEach(row => {{
    const source = document.getElementById('priceSource').value;
    const price = Number(row.dataset[source]);
    const required = Number.isFinite(price) && price > 1 && target > 0 ? target / price : NaN;
    const checkbox = row.querySelector('.team-select'); checkbox.disabled = !Number.isFinite(required); row.classList.toggle('selected', checkbox.checked && Number.isFinite(required));
    row.querySelector('.selected-price').textContent = Number.isFinite(price) ? price.toFixed(2) : '—';
    row.querySelector('.required').textContent = Number.isFinite(required) ? required.toFixed(2) : '—';
    row.querySelector('.gross').textContent = Number.isFinite(required) ? (required * price).toFixed(2) : '—';
    const net = Number.isFinite(required) ? target - required : NaN;
    const netCell = row.querySelector('.net'); netCell.textContent = Number.isFinite(net) ? net.toFixed(2) : '—';
    netCell.className = 'net ' + (net >= 0 ? 'positive' : 'negative');
    if (checkbox.checked && Number.isFinite(required)) {{ selectedCount += 1; selectedOutlay += required; }}
  }});
  document.getElementById('selectedCount').textContent = selectedCount;
  document.getElementById('selectedOutlay').textContent = selectedCount ? selectedOutlay.toFixed(2) : '—';
  document.getElementById('selectedGross').textContent = selectedCount && target > 0 ? target.toFixed(2) : '—';
  const selectedNet = selectedCount && target > 0 ? target - selectedOutlay : NaN;
  const selectedNetElement = document.getElementById('selectedNet'); selectedNetElement.textContent = Number.isFinite(selectedNet) ? selectedNet.toFixed(2) : '—';
  selectedNetElement.style.color = Number.isFinite(selectedNet) && selectedNet >= 0 ? 'var(--accent)' : 'var(--warn)';
}}
document.getElementById('target').addEventListener('input', updateCalculations);
document.getElementById('priceSource').addEventListener('change', updateCalculations);
document.querySelectorAll('.team-select').forEach(input => input.addEventListener('change', updateCalculations));
updateCalculations();
</script>
</main></body></html>"""


def _premier_league_teams():
    """Use current API fixture data to discover real Premier League teams."""
    fallback = [
        "Arsenal", "Manchester United", "Tottenham Hotspur", "Chelsea",
        "Liverpool", "Manchester City",
    ]
    try:
        rows = _live_rows("soccer_epl")
        names = sorted({
            team
            for event, _market, _quote in rows
            for team in (event.home_team, event.away_team)
        })
        if names:
            return names, "Team names loaded from current Premier League fixture data via the read-only API."
        return fallback, "The API returned no current fixtures, so example teams are shown."
    except OddsApiError:
        return fallback, "The API team lookup was unavailable, so example teams are shown."


def _dashboard(sport_key: str, market: str = "h2h", demo: bool = False, force_refresh: bool = False) -> str:
    title = SPORTS.get(sport_key, sport_key)
    market_title = MARKETS.get(market, MARKETS["h2h"])
    status = "Live API data"
    status_detail = "Read-only request using the Australian bookmaker region."
    error = ""
    if demo:
        rows = [row for row in _sample_rows() if row[1].market_type == market]
        status = "Presentation sample data"
        status_detail = "Synthetic records shown explicitly for layout demonstration."
    else:
        try:
            rows = _live_rows(sport_key, markets=market, force_refresh=force_refresh)
            if not rows:
                status = "No live data available"
                status_detail = "The provider returned no current records for this competition."
        except OddsApiError as exc:
            rows = []
            status = "Live data unavailable"
            status_detail = "The provider request could not be completed."
            error = str(exc)

    events = {}
    quotes_by_event = defaultdict(list)
    for event, market, quote in rows:
        events[event.event_id] = event
        quotes_by_event[event.event_id].append((market, quote))

    quality_items = "".join(
        f'<li class="{level}"><span>{escape(label)}</span><b>{value}</b></li>'
        for label, value, level in _quality_checks(rows)
    )

    cards = []
    for event in events.values():
        quotes = quotes_by_event[event.event_id]
        outcomes = defaultdict(list)
        bookmakers = set()
        comparison = defaultdict(dict)
        for market, quote in quotes:
            outcomes[quote.outcome].append(quote.price)
            source_name = market.source_name or (market.source_market_id.split(":", 1)[0] if market.source_market_id else market.source)
            bookmakers.add(source_name)
            comparison[quote.outcome][source_name] = quote.price
        outcome_rows = []
        source_columns = sorted(bookmakers)
        spreads = {
            outcome: max(prices.values()) - min(prices.values())
            for outcome, prices in comparison.items() if len(prices) > 1
        }
        largest_spread = max(spreads.values(), default=Decimal("0"))

        def outcome_label(outcome: str) -> str:
            lowered = outcome.casefold()
            if lowered in {"home", event.home_team.casefold()}:
                return f"{event.home_team} win"
            if lowered in {"away", event.away_team.casefold()}:
                return f"{event.away_team} win"
            if lowered == "draw":
                return "Draw"
            return outcome

        def outcome_rank(outcome: str) -> tuple[int, str]:
            lowered = outcome.casefold()
            if market == "totals":
                if lowered.startswith("over"):
                    return (0, "")
                if lowered.startswith("under"):
                    return (1, "")
            if lowered in {"home", event.home_team.casefold()}:
                return (0, "")
            if lowered == "draw":
                return (1, "")
            if lowered in {"away", event.away_team.casefold()}:
                return (2, "")
            return (3, lowered)

        for outcome, prices in sorted(outcomes.items(), key=lambda item: outcome_rank(item[0])):
            source_prices = "".join(
                f"<td>{comparison[outcome].get(source, ''):.2f}</td>" if source in comparison[outcome] else "<td>—</td>"
                for source in source_columns
            )
            is_highlight = largest_spread > 0 and spreads.get(outcome) == largest_spread
            difference = spreads.get(outcome, Decimal("0"))
            label = f"<strong>{escape(outcome_label(outcome))}</strong>" if is_highlight else escape(outcome_label(outcome))
            difference_cell = f'<td class="difference">{difference:.2f}</td>'
            outcome_rows.append(f"<tr{' class=\"highlight-row\"' if is_highlight else ''}><td>{label}</td>{source_prices}{difference_cell}</tr>")
        headers = "".join(f"<th>{escape(source)}</th>" for source in source_columns) + "<th>Difference</th>"
        cards.append(f"""
        <article class="event">
          <div class="event-head"><h2>{escape(event.home_team)} <span>vs</span> {escape(event.away_team)}</h2>
          <p>{_format_time(event.start_time)}</p></div>
          <div class="event-meta"><span>{escape(event.competition)}</span><span>{escape(market_title)}</span><span>{len(bookmakers)} source(s)</span><span>{len(quotes)} quote(s)</span></div>
          <table><caption>Same market and outcome across sources</caption><thead><tr><th>Outcome</th>{headers}</tr></thead><tbody>{''.join(outcome_rows)}</tbody></table>
        </article>""")

    error_html = f'<p class="notice error">{escape(error)}</p>' if error else ""
    options = "".join(
        f'<option value="{escape(key)}"{" selected" if key == sport_key else ""}>{escape(label)}</option>'
        for key, label in SPORTS.items()
    )
    market_options = "".join(
        f'<option value="{escape(key)}"{" selected" if key == market else ""}>{escape(label)}</option>'
        for key, label in MARKETS.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fun Football — Market Monitor</title>
<style>
  :root {{ color-scheme: dark; --bg:#10131a; --panel:#191e28; --line:#303847; --text:#f3f5f7; --muted:#aab3c1; --accent:#64d6a0; --warn:#f4c56d; }}
  * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,sans-serif; }}
  main {{ width:100%; max-width:none; margin:0; padding:42px 32px 64px; }} header {{ display:flex; justify-content:space-between; gap:20px; align-items:end; flex-wrap:wrap; margin-bottom:28px; }}
  h1 {{ margin:0; font-size:32px; letter-spacing:-.03em; }} h1 small {{ color:var(--accent); font-size:13px; display:block; letter-spacing:.12em; text-transform:uppercase; margin-bottom:8px; }}
  .controls {{ display:flex; gap:10px; align-items:end; }} label {{ color:var(--muted); font-size:12px; display:grid; gap:5px; }} select,button {{ background:var(--panel); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font:inherit; }} button {{ cursor:pointer; background:var(--accent); color:#0d1712; border-color:var(--accent); font-weight:650; }}
  .status {{ border:1px solid var(--line); background:var(--panel); border-radius:12px; padding:16px; margin-bottom:22px; }} .status small {{ display:block; color:var(--muted); letter-spacing:.1em; font-size:11px; margin-bottom:4px; }} .status strong {{ color:var(--accent); }} .status p {{ margin:3px 0 0; color:var(--muted); }} .notice {{ color:var(--warn); }} .error {{ color:#ff9f9f; }}
  .quality {{ border:1px solid var(--line); background:var(--panel); border-radius:12px; padding:16px; margin-bottom:22px; }} .quality h2 {{ font-size:16px; margin:0 0 10px; }} .quality ul {{ display:grid; grid-template-columns:repeat(5,1fr); gap:8px; padding:0; margin:0; list-style:none; }} .quality li {{ background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:10px; }} .quality li span {{ display:block; color:var(--muted); font-size:11px; }} .quality li b {{ display:block; margin-top:4px; font-size:18px; color:var(--accent); }} .quality li.warning b {{ color:var(--warn); }}
  .summary {{ display:flex; gap:10px; flex-wrap:wrap; margin:0 0 22px; }} .summary div {{ min-width:125px; background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px 14px; }} .summary b {{ display:block; color:var(--accent); font-size:20px; }} .summary span {{ color:var(--muted); font-size:12px; }}
  .events {{ display:grid; grid-template-columns:1fr; gap:16px; }} .event {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:18px; }}
  .event-head {{ display:flex; justify-content:space-between; gap:12px; align-items:start; }} h2 {{ font-size:18px; margin:0; }} h2 span {{ color:var(--muted); font-size:13px; font-weight:400; }} .event-head p {{ color:var(--muted); font-size:12px; margin:2px 0 0; white-space:nowrap; }}
  .event-meta {{ display:flex; flex-wrap:wrap; gap:8px 14px; color:var(--muted); font-size:12px; border-bottom:1px solid var(--line); padding:12px 0; margin-bottom:10px; }} table {{ width:100%; min-width:1180px; table-layout:fixed; border-collapse:collapse; font-size:13px; }} caption {{ text-align:left; color:var(--muted); font-size:12px; padding:0 0 6px; }} th,td {{ text-align:left; padding:7px 12px 7px 0; border-bottom:1px solid var(--line); vertical-align:top; overflow-wrap:anywhere; }} th:first-child,td:first-child {{ width:180px; }} th:last-child,td:last-child {{ width:105px; }} th {{ color:var(--muted); font-weight:500; }} td:not(:first-child) {{ color:var(--accent); }} .difference {{ color:var(--warn) !important; font-weight:650; }} .highlight-row td {{ background:rgba(100,214,160,.08); }}
  .empty {{ color:var(--muted); padding:32px 0; }} footer {{ color:var(--muted); font-size:12px; margin-top:30px; }}
  @media(max-width:600px) {{ main {{ padding:28px 14px; }} .controls {{ width:100%; }} label,select,button {{ width:100%; }} .event-head {{ display:block; }} .event-head p {{ margin-top:8px; }} .quality ul {{ grid-template-columns:repeat(2,1fr); }} }}
</style></head><body><main>
<header><div><h1><small>Fun Football</small>Market monitor</h1></div>
<form class="controls" method="get"><input type="hidden" name="refresh" value="1"><label>Competition<select name="sport_key">{options}</select></label><label>Market<select name="market">{market_options}</select></label><button type="submit">Request latest data</button></form></header>
<section class="status" aria-live="polite"><small>DATA SOURCE</small><strong>{escape(status)}</strong><p>{escape(status_detail)}</p>{error_html}</section>
<section class="quality" aria-label="Data quality checks"><h2>Data quality checks</h2><ul>{quality_items}</ul></section>
<section class="summary" aria-label="Dashboard summary"><div><b>{len(events)}</b><span>event(s)</span></div><div><b>{len(rows)}</b><span>quote(s)</span></div><div><b>{escape(title)}</b><span>competition</span></div></section>
<p><a href="/?view=scenario">Open theoretical scenario analysis →</a></p>
<section class="events">{''.join(cards) if cards else '<p class="empty">No events available for this selection.</p>'}</section>
<footer>For practice, research, fun and curiosity. Highlighted rows show the largest observed difference across sources; they are not recommendations. No transactions are provided.</footer>
</main></body></html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        query = parse_qs(urlparse(self.path).query)
        if query.get("view", [""])[0] == "afl-premiers":
            force_refresh = query.get("refresh", ["0"])[0] == "1"
            body = _afl_premiers_dashboard(force_refresh=force_refresh).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if query.get("view", [""])[0] == "scenario":
            team_names, team_source = _premier_league_teams()
            body = _scenario_dashboard(team_names, team_source).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        sport_key = query.get("sport_key", ["soccer_epl"])[0]
        if sport_key not in SPORTS:
            sport_key = "soccer_epl"
        demo = query.get("demo", ["0"])[0] == "1"
        force_refresh = query.get("refresh", ["0"])[0] == "1"
        market = query.get("market", ["h2h"])[0]
        if market not in MARKETS:
            market = "h2h"
        body = _dashboard(sport_key, market=market, demo=demo, force_refresh=force_refresh).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        return


if __name__ == "__main__":
    print("Fun Football dashboard: http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), DashboardHandler).serve_forever()
