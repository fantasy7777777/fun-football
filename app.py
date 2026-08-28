"""Small local presentation dashboard for Fun Football."""

from collections import defaultdict
from decimal import Decimal
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fun_football.csv_importer import load_market_csv
from fun_football.odds_api import OddsApiError, TheOddsApiClient


SPORTS = {
    "soccer_epl": "Premier League",
    "soccer_australia_aleague": "A-League",
    "aussierules_afl": "AFL",
    "aussierules_aflw": "AFLW",
}


def _format_time(value) -> str:
    return value.strftime("%d %b %Y, %H:%M UTC")


def _live_rows(sport_key: str):
    return TheOddsApiClient().get_odds(sport_key=sport_key, regions="au", markets="h2h")


def _sample_rows():
    return load_market_csv(Path("data/examples/market_quotes.csv"))


def _dashboard(sport_key: str, demo: bool = False) -> str:
    title = SPORTS.get(sport_key, sport_key)
    status = "Live API data"
    status_detail = "Read-only request using the Australian bookmaker region."
    error = ""
    if demo:
        rows = _sample_rows()
        status = "Presentation sample data"
        status_detail = "Synthetic records shown explicitly for layout demonstration."
    else:
        try:
            rows = _live_rows(sport_key)
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

        for outcome, prices in sorted(outcomes.items()):
            source_prices = "".join(
                f"<td>{comparison[outcome].get(source, ''):.2f}</td>" if source in comparison[outcome] else "<td>—</td>"
                for source in source_columns
            )
            is_highlight = largest_spread > 0 and spreads.get(outcome) == largest_spread
            label = f"<strong>{escape(outcome_label(outcome))}</strong>" if is_highlight else escape(outcome_label(outcome))
            note = f" <small class=\"highlight\">largest observed difference: {largest_spread:.2f}</small>" if is_highlight else ""
            outcome_rows.append(f"<tr{' class=\"highlight-row\"' if is_highlight else ''}><td>{label}{note}</td>{source_prices}</tr>")
        headers = "".join(f"<th>{escape(source)}</th>" for source in source_columns)
        cards.append(f"""
        <article class="event">
          <div class="event-head"><h2>{escape(event.home_team)} <span>vs</span> {escape(event.away_team)}</h2>
          <p>{_format_time(event.start_time)}</p></div>
          <div class="event-meta"><span>{escape(event.competition)}</span><span>{len(bookmakers)} source(s)</span><span>{len(quotes)} quote(s)</span></div>
          <table><caption>Same market and outcome across sources</caption><thead><tr><th>Outcome</th>{headers}</tr></thead><tbody>{''.join(outcome_rows)}</tbody></table>
        </article>""")

    error_html = f'<p class="notice error">{escape(error)}</p>' if error else ""
    options = "".join(
        f'<option value="{escape(key)}"{" selected" if key == sport_key else ""}>{escape(label)}</option>'
        for key, label in SPORTS.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fun Football — Market Monitor</title>
<style>
  :root {{ color-scheme: dark; --bg:#10131a; --panel:#191e28; --line:#303847; --text:#f3f5f7; --muted:#aab3c1; --accent:#64d6a0; --warn:#f4c56d; }}
  * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,sans-serif; }}
  main {{ max-width:1050px; margin:0 auto; padding:42px 22px 64px; }} header {{ display:flex; justify-content:space-between; gap:20px; align-items:end; flex-wrap:wrap; margin-bottom:28px; }}
  h1 {{ margin:0; font-size:32px; letter-spacing:-.03em; }} h1 small {{ color:var(--accent); font-size:13px; display:block; letter-spacing:.12em; text-transform:uppercase; margin-bottom:8px; }}
  .controls {{ display:flex; gap:10px; align-items:end; }} label {{ color:var(--muted); font-size:12px; display:grid; gap:5px; }} select,button {{ background:var(--panel); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font:inherit; }} button {{ cursor:pointer; background:var(--accent); color:#0d1712; border-color:var(--accent); font-weight:650; }}
  .status {{ border:1px solid var(--line); background:var(--panel); border-radius:12px; padding:16px; margin-bottom:22px; }} .status strong {{ color:var(--accent); }} .status p {{ margin:3px 0 0; color:var(--muted); }} .notice {{ color:var(--warn); }} .error {{ color:#ff9f9f; }}
  .summary {{ display:flex; gap:10px; flex-wrap:wrap; margin:0 0 22px; }} .summary div {{ min-width:125px; background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px 14px; }} .summary b {{ display:block; color:var(--accent); font-size:20px; }} .summary span {{ color:var(--muted); font-size:12px; }}
  .events {{ display:grid; grid-template-columns:1fr; gap:16px; }} .event {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:18px; }}
  .event-head {{ display:flex; justify-content:space-between; gap:12px; align-items:start; }} h2 {{ font-size:18px; margin:0; }} h2 span {{ color:var(--muted); font-size:13px; font-weight:400; }} .event-head p {{ color:var(--muted); font-size:12px; margin:2px 0 0; white-space:nowrap; }}
  .event-meta {{ display:flex; flex-wrap:wrap; gap:8px 14px; color:var(--muted); font-size:12px; border-bottom:1px solid var(--line); padding:12px 0; margin-bottom:10px; }} table {{ width:100%; border-collapse:collapse; font-size:13px; }} caption {{ text-align:left; color:var(--muted); font-size:12px; padding:0 0 6px; }} th,td {{ text-align:left; padding:7px 8px 7px 0; border-bottom:1px solid var(--line); vertical-align:top; }} th {{ color:var(--muted); font-weight:500; }} td:not(:first-child) {{ color:var(--accent); }} .highlight-row td {{ background:rgba(100,214,160,.08); }} .highlight {{ color:var(--warn); font-weight:500; }}
  .empty {{ color:var(--muted); padding:32px 0; }} footer {{ color:var(--muted); font-size:12px; margin-top:30px; }}
  @media(max-width:600px) {{ main {{ padding:28px 14px; }} .controls {{ width:100%; }} label,select,button {{ width:100%; }} .event-head {{ display:block; }} .event-head p {{ margin-top:8px; }} }}
</style></head><body><main>
<header><div><h1><small>Fun Football</small>Market monitor</h1></div>
<form class="controls" method="get"><label>Competition<select name="sport_key">{options}</select></label><button type="submit">Request latest data</button></form></header>
<section class="status" aria-live="polite"><strong>{escape(status)}</strong><p>{escape(status_detail)}</p>{error_html}</section>
<section class="summary" aria-label="Dashboard summary"><div><b>{len(events)}</b><span>event(s)</span></div><div><b>{len(rows)}</b><span>quote(s)</span></div><div><b>{escape(title)}</b><span>competition</span></div></section>
<section class="events">{''.join(cards) if cards else '<p class="empty">No events available for this selection.</p>'}</section>
<footer>For practice, research, fun and curiosity. Highlighted rows show the largest observed difference across sources; they are not recommendations. No transactions are provided.</footer>
</main></body></html>"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        query = parse_qs(urlparse(self.path).query)
        sport_key = query.get("sport_key", ["soccer_epl"])[0]
        if sport_key not in SPORTS:
            sport_key = "soccer_epl"
        demo = query.get("demo", ["0"])[0] == "1"
        body = _dashboard(sport_key, demo=demo).encode("utf-8")
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
