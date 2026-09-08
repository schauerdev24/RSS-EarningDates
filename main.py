"""
main.py — one long-running Railway worker.

  * Monday MONDAY_HOUR (local TZ): earnings-date email to each analyst.
  * Always: polls EDGAR every POLL_SECONDS, emails the covering analyst
    the moment one of our names files an 8-K / 10-Q / 10-K.

Local testing:
  python main.py --dry-run     print the Monday emails, send nothing
  python main.py --send-now    send the Monday emails immediately, then exit
"""
import logging
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
import edgar
import tickers
from earnings import send_monday_emails

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("main")


def main():
    if "--dry-run" in sys.argv:
        send_monday_emails(dry_run=True)
        return
    config.check()
    if "--send-now" in sys.argv:
        send_monday_emails()
        return

    names = tickers.load()
    log.info("loaded %d names (%d watchlist)",
             len(names), sum(n.watchlist for n in names.values()))

    sched = BackgroundScheduler(timezone=config.TZ)
    sched.add_job(send_monday_emails, CronTrigger(
        day_of_week="mon", hour=config.MONDAY_HOUR, minute=config.MONDAY_MINUTE),
        misfire_grace_time=3600)
    sched.start()
    log.info("Monday email scheduled %02d:%02d %s",
             config.MONDAY_HOUR, config.MONDAY_MINUTE, config.TZ)

    edgar.poll_forever(names)          # blocks forever


if __name__ == "__main__":
    main()
