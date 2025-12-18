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


def send_price_drop_email(to_email: str, subject: str, html_body: str, dry_run: bool = False) -> bool:
    """
    Send a price-drop email via Gmail SMTP.

    If dry_run is True, this will only log what would be sent.
    
    Returns:
        True if email was sent successfully (or dry_run), False otherwise
    """
    if dry_run:
        print(f"[DRY RUN] Would send price-drop email to {to_email} with subject '{subject}'.")
        return True

    creds = _get_gmail_credentials()
    if creds is None:
        # Already logged a helpful message
        print(f"ERROR: Cannot send price-drop email to {to_email} - Gmail credentials missing")
        return False

    user, app_password = creds

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(user, app_password)
            server.send_message(msg)
        print(f"✓ Successfully sent price-drop email to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ ERROR: SMTP Authentication failed when sending to {to_email}: {e}")
        print(f"  Check that GMAIL_USER and GMAIL_APP_PASSWORD are correct")
        return False
    except smtplib.SMTPException as e:
        print(f"✗ ERROR: SMTP error when sending to {to_email}: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: Unexpected error sending email to {to_email}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

