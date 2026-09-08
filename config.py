"""All settings come from Railway environment variables. See .env.example."""
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
TICKER_FILE = HERE / "eps_tickers.txt"

# Office 365 mailbox that sends the alerts (IT must enable SMTP AUTH on it)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")          # alerts@yourfund.com
SMTP_PASS = os.environ.get("SMTP_PASS", "")          # its password / app password
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)

# {"Will": "will@fund.com", "Cory": "...", "Tony": "...", "Humberto": "..."}
ANALYST_EMAILS = json.loads(os.environ.get("ANALYST_EMAILS", "{}"))
UNASSIGNED_OWNER = os.environ.get("UNASSIGNED_OWNER", "Humberto")
# optional: gets a copy of every filing alert and every Monday email
CC_ALL = [e.strip() for e in os.environ.get("CC_ALL", "").split(",") if e.strip()]

# SEC requires "Company Name contact@email.com"
SEC_USER_AGENT = os.environ.get("SEC_USER_AGENT", "")
ALERT_FORMS = {f.strip() for f in os.environ.get(
    "ALERT_FORMS", "8-K,8-K/A,10-Q,10-Q/A,10-K,10-K/A").split(",")}
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "10"))

TZ = os.environ.get("TZ", "America/New_York")
MONDAY_HOUR = int(os.environ.get("MONDAY_HOUR", "7"))     # 7 = 7:00 AM local
MONDAY_MINUTE = int(os.environ.get("MONDAY_MINUTE", "0"))

# yfinance / EDGAR symbol fixes
FIX = {"BRKB": "BRK-B", "BRK.B": "BRK-B"}


def check():
    missing = [k for k, v in {"SMTP_USER": SMTP_USER, "SMTP_PASS": SMTP_PASS,
                              "SEC_USER_AGENT": SEC_USER_AGENT}.items() if not v]
    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}")
    if not ANALYST_EMAILS:
        raise SystemExit("ANALYST_EMAILS is empty — set it as a JSON object.")
