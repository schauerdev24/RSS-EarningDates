"""eps_tickers.txt -> who covers what. Same format as the dashboard repo."""
from dataclasses import dataclass

from config import ANALYST_EMAILS, CC_ALL, TICKER_FILE, UNASSIGNED_OWNER


@dataclass
class Name:
    ticker: str
    owner: str          # analyst name, or UNASSIGNED_OWNER
    watchlist: bool


def load() -> dict[str, Name]:
    names, section = {}, "portfolio"
    for raw in open(TICKER_FILE):
        s = raw.strip()
        if s.lower().startswith("# watch"):
            section = "watch"; continue
        if s.lower().startswith("# portfolio"):
            section = "portfolio"; continue
        if not s or s.startswith("#"):
            continue
        t, _, p = s.partition(",")
        t, p = t.strip().upper(), p.strip()
        if t not in names:
            names[t] = Name(t, p or UNASSIGNED_OWNER, section == "watch")
    return names


def email_for(owner: str) -> str | None:
    return ANALYST_EMAILS.get(owner) or ANALYST_EMAILS.get(UNASSIGNED_OWNER)


def recipients(tickers: list[str], names: dict[str, Name]) -> list[str]:
    """Union of covering analysts for one or more tickers (GOOG+GOOGL etc)."""
    out = []
    for t in tickers:
        e = email_for(names[t].owner) if t in names else None
        if e and e not in out:
            out.append(e)
    for e in CC_ALL:
        if e not in out:
            out.append(e)
    return out
