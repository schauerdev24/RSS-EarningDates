# edgar-alerts

One Railway worker, two jobs:

1. **Monday 7:00 AM ET** — pulls next earnings dates (yfinance) for every name in
   `eps_tickers.txt` and emails each analyst *their* names (green = reports this
   week), plus the watchlist. Names with no analyst go to `UNASSIGNED_OWNER`.
2. **Every 10 seconds, all day** — polls EDGAR's latest-filings feed. The moment
   one of our companies files an 8-K / 10-Q / 10-K, the covering analyst gets
   an email with the link. Watchlist + unassigned filings go to `UNASSIGNED_OWNER`.

## Deploy (Railway)

1. Push this folder to GitHub, "New Project → Deploy from repo" in Railway.
2. Add the variables from `.env.example`. Railway runs `Procfile` → `python main.py`.
3. Email goes out through Office 365 SMTP from the `SMTP_USER` mailbox. IT must
   turn on **Authenticated SMTP** for that mailbox (Exchange admin center →
   Mailboxes → pick it → Manage email apps). If MFA is on, use an app password.
4. `SEC_USER_AGENT` is required by the SEC (company name + contact email).

## Maintain

* Edit `eps_tickers.txt` (same format as the dashboard repo: `TICKER,Analyst`),
  commit, Railway redeploys.
* Test locally: `python main.py --dry-run` prints the Monday emails;
  `python main.py --send-now` sends them for real.
* Tickers without an SEC CIK (OTC ADRs like PROSY, preferreds) still get
  earnings dates but no filing alerts — check the startup log for warnings.
