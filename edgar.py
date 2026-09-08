"""Polls EDGAR's latest-filings Atom feed and emails the covering analyst."""
import collections
import datetime as dt
import logging
import re
import time
from html import escape

import feedparser
import requests

import mailer
from config import ALERT_FORMS, FIX, POLL_SECONDS, SEC_USER_AGENT
from tickers import Name, recipients

log = logging.getLogger("edgar")

FEED_URL = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
            "&type=&company=&dateb=&owner=include&start=0&count=100&output=atom")
CIK_URL = "https://www.sec.gov/files/company_tickers.json"
HEADERS = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
CIK_RE = re.compile(r"\((\d{10})\)")


def load_cik_map(names: dict[str, Name]) -> dict[str, list[str]]:
    """CIK (10-digit string) -> our tickers with that CIK (GOOG & GOOGL share one)."""
    r = requests.get(CIK_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    by_ticker = {row["ticker"].upper(): f'{row["cik_str"]:010d}'
                 for row in r.json().values()}
    out: dict[str, list[str]] = {}
    for t in names:
        cik = by_ticker.get(FIX.get(t, t).replace(".", "-"))
        if cik:
            out.setdefault(cik, []).append(t)
        else:
            log.warning("no CIK for %s (OTC/ADR/preferred?) — no filing alerts", t)
    log.info("watching %d CIKs for %d tickers", len(out), sum(map(len, out.values())))
    return out


def _parse(entry):
    """title looks like '8-K - APPLE INC (0000320193) (Filer)'"""
    title = entry.get("title", "")
    form, _, rest = title.partition(" - ")
    m = CIK_RE.search(rest)
    company = rest[:m.start()].strip() if m else rest
    return form.strip(), (m.group(1) if m else None), company


def _alert(form, company, tickers, entry, names):
    to = recipients(tickers, names)
    tk = "/".join(tickers)
    html = (f'<div style="font-family:Arial;font-size:14px">'
            f"<h2>{escape(tk)} filed a {escape(form)}</h2>"
            f"<p><b>{escape(company)}</b></p>"
            f"<p>Filed: {escape(entry.get('updated', ''))}</p>"
            f'<p><a href="{escape(entry.link)}">Open filing on EDGAR</a></p></div>')
    mailer.send(to, f"[EDGAR] {tk} — {form} filed", html)


def poll_forever(names: dict[str, Name]) -> None:
    cik_map = load_cik_map(names)
    cik_loaded = time.time()
    seen: set[str] = set()
    order: collections.deque = collections.deque(maxlen=5000)
    first = True
    log.info("polling EDGAR every %ss for forms %s", POLL_SECONDS, sorted(ALERT_FORMS))

    while True:
        try:
            if time.time() - cik_loaded > 86400:          # refresh CIK map daily
                cik_map, cik_loaded = load_cik_map(names), time.time()
            r = requests.get(FEED_URL, headers=HEADERS, timeout=20)
            r.raise_for_status()
            feed = feedparser.parse(r.text)
            for entry in reversed(feed.entries):          # oldest first
                key = entry.get("id") or entry.link
                if key in seen:
                    continue
                seen.add(key)
                if len(order) == order.maxlen:
                    seen.discard(order[0])
                order.append(key)
                if first:
                    continue                              # don't spam on boot
                form, cik, company = _parse(entry)
                if form in ALERT_FORMS and cik in cik_map:
                    log.info("HIT %s %s %s", form, cik_map[cik], company)
                    _alert(form, company, cik_map[cik], entry, names)
            first = False
        except Exception as e:
            log.error("poll error: %s", e)
            time.sleep(30)
            continue
        time.sleep(POLL_SECONDS)
