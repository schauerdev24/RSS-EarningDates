"""One function: send(to, subject, html) via Office 365 SMTP."""
import logging
import smtplib
from email.message import EmailMessage

from config import SMTP_HOST, SMTP_PASS, SMTP_PORT, SMTP_USER, FROM_EMAIL

log = logging.getLogger("mailer")


def send(to: list[str], subject: str, html: str) -> None:
    if not to:
        log.warning("no recipients for %r — skipped", subject)
        return
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = FROM_EMAIL, ", ".join(to), subject
    msg.set_content("This email is HTML — open in a mail client that renders it.")
    msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        log.info("sent %r -> %s", subject, ", ".join(to))
    except smtplib.SMTPAuthenticationError as e:
        log.error("SMTP login failed — ask IT to enable SMTP AUTH on %s "
                  "(Exchange admin → mailbox → Manage email apps → Authenticated SMTP): %s",
                  SMTP_USER, e)
    except Exception as e:
        log.error("SMTP error: %s", e)
