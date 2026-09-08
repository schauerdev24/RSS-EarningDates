"""Monday job: yfinance earnings dates -> one email per analyst."""
import datetime as dt
import logging
from html import escape
from zoneinfo import ZoneInfo

import yfinance as yf

import mailer
from config import CC_ALL, FIX, TZ, UNASSIGNED_OWNER
from tickers import Name, email_for, load

log = logging.getLogger("earnings")


def next_earnings(symbol: str) -> dt.date | None:
    yq = FIX.get(symbol, symbol)
    try:
        cal = yf.Ticker(yq).calendar
        dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
        if dates:
            d = dates[0]
            return dt.date(d.year, d.month, d.day)
    except Exception:
        pass
    try:
        df = yf.Ticker(yq).get_earnings_dates(limit=8)
        if df is not None and len(df):
            future = [ix.date() for ix in df.index if ix.date() >= dt.date.today()]
            if future:
                return min(future)
    except Exception:
        pass
    return None


def company_name(symbol: str) -> str:
    try:
        return yf.Ticker(FIX.get(symbol, symbol)).info.get("longName") or symbol
    except Exception:
        return symbol


def fetch_all(names: dict[str, Name]) -> dict[str, tuple[str, dt.date | None]]:
    out = {}
    for t in names:
        d = next_earnings(t)
        out[t] = (company_name(t), d)
        log.info("  %-8s %s", t, d.strftime("%a %m/%d/%Y") if d else "-- no date")
    return out


def _table(rows, today: dt.date) -> str:
    monday = today - dt.timedelta(days=today.weekday())
    sunday = monday + dt.timedelta(days=6)
    rows = sorted(rows, key=lambda r: (r[2] is None, r[2] or dt.date.max))
    body = []
    for i, (t, co, d) in enumerate(rows):
        this_week = d is not None and monday <= d <= sunday
        bg = "#C6EFCE" if this_week else ("#DDEBF7" if i % 2 == 0 else "#FFFFFF")
        weight = "bold" if this_week else "normal"
        ds = d.strftime("%A, %B %d, %Y") if d else "—"
        body.append(
            f'<tr style="background:{bg};font-weight:{weight}">'
            f"<td>{escape(t)}</td><td>{escape(co)}</td><td>{ds}</td></tr>")
    return (
        '<table cellpadding="6" style="border-collapse:collapse;font-family:Arial;'
        'font-size:13px"><tr style="background:#1F4E78;color:#fff;font-weight:bold">'
        "<th>Ticker</th><th>Company</th><th>Earnings Date</th></tr>"
        + "".join(body) + "</table>")


def send_monday_emails(dry_run: bool = False) -> None:
    today = dt.datetime.now(ZoneInfo(TZ)).date()
    names = load()
    log.info("fetching earnings dates for %d names", len(names))
    data = fetch_all(names)

    by_owner: dict[str, list] = {}
    watch = []
    for t, n in names.items():
        row = (t, *data[t])
        (watch if n.watchlist else by_owner.setdefault(n.owner, [])).append(row)

    watch_html = f"<h3>Watchlist</h3>{_table(watch, today)}" if watch else ""
    for owner, rows in by_owner.items():
        to = [e for e in [email_for(owner)] if e] + CC_ALL
        label = "Unassigned names" if owner == UNASSIGNED_OWNER else f"{owner}'s names"
        html = (f'<div style="font-family:Arial">'
                f"<h2>Earnings this week — {escape(label)}</h2>"
                f"<p>Week of {today:%B %d, %Y}. Green = reports this week.</p>"
                f"{_table(rows, today)}{watch_html}</div>")
        subject = f"Earnings dates — {owner} — week of {today:%m/%d}"
        if dry_run:
            print(f"\n=== {subject} -> {to}\n{html}\n")
        else:
            mailer.send(to, subject, html)
