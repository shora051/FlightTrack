"""
Mail utilities for sending transactional emails via Mailgun.
"""
import requests
from flask import current_app


def send_mailgun_email(to: str, subject: str, text: str, html: str | None = None) -> bool:
    """
    Send an email through Mailgun.

    Returns True on success, False otherwise.
    """
    api_key = current_app.config.get('MAILGUN_API_KEY')
    domain = current_app.config.get('MAILGUN_DOMAIN')
    from_email = current_app.config.get('MAILGUN_FROM_EMAIL')
    base_url = current_app.config.get('MAILGUN_BASE_URL', 'https://api.mailgun.net/v3')

    if not api_key or not domain or not from_email:
        print("Mailgun configuration missing; cannot send email.")
        return False

    url = f"{base_url}/{domain}/messages"
    data = {
        "from": from_email,
        "to": [to],
        "subject": subject,
        "text": text,
    }
    if html:
        data["html"] = html

    try:
        response = requests.post(url, auth=("api", api_key), data=data, timeout=10)
        if response.status_code == 200:
            return True
        print(f"Mailgun send failed ({response.status_code}): {response.text}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"Error sending Mailgun email: {exc}")
        return False

