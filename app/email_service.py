import os
import smtplib
from email.mime.text import MIMEText
from typing import Optional


def _get_gmail_credentials() -> Optional[tuple[str, str]]:
    """
    Fetch Gmail SMTP credentials from environment.

    Expects:
    - GMAIL_USER
    - GMAIL_APP_PASSWORD
    """
    user = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not user or not app_password:
        print("Gmail SMTP not configured: GMAIL_USER and/or GMAIL_APP_PASSWORD missing.")
        return None

    return user, app_password


def send_price_drop_email(to_email: str, subject: str, html_body: str, dry_run: bool = False) -> None:
    """
    Send a price-drop email via Gmail SMTP.

    If dry_run is True, this will only log what would be sent.
    """
    if dry_run:
        print(f"[DRY RUN] Would send price-drop email to {to_email} with subject '{subject}'.")
        return

    creds = _get_gmail_credentials()
    if creds is None:
        # Already logged a helpful message
        return

    user, app_password = creds

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(user, app_password)
            server.send_message(msg)
        print(f"Sent price-drop email to {to_email}")
    except Exception as e:
        print(f"Error sending email via Gmail SMTP: {e}")

