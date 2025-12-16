"""
Mail utilities for sending transactional emails via Gmail SMTP.
"""
from email.message import EmailMessage
import smtplib

from flask import current_app


def send_email(to: str, subject: str, text: str, html: str | None = None) -> bool:
    """
    Send an email using Gmail SMTP.

    Returns True on success, False otherwise.
    """
    smtp_server = current_app.config.get('GMAIL_SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('GMAIL_SMTP_PORT', 587)
    username = current_app.config.get('GMAIL_USERNAME')
    app_password = current_app.config.get('GMAIL_APP_PASSWORD')
    from_email = current_app.config.get('GMAIL_FROM_EMAIL', username)

    if not username or not app_password or not from_email:
        print("Gmail configuration missing; cannot send email.")
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to
    msg.set_content(text or "")

    if html:
        msg.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(username, app_password)
            server.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Error sending Gmail email: {exc}")
        return False
