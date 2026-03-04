import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def send_approval_request(username: str, user_email: str, approval_token: str) -> None:
    """Send admin notification email with one-click approve/reject links."""
    if not settings.gmail_sender or not settings.gmail_app_password:
        # Email not configured — skip silently (log to console)
        print(f"[EMAIL SKIPPED] Approval token for {username}: {approval_token}")
        print(f"  Approve: {settings.backend_url}/auth/approve/{approval_token}")
        print(f"  Reject:  {settings.backend_url}/auth/reject/{approval_token}")
        return

    approve_url = f"{settings.backend_url}/auth/approve/{approval_token}"
    reject_url = f"{settings.backend_url}/auth/reject/{approval_token}"

    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
      <h2 style="color: #1da1f2;">New User Registration — F&amp;O Trader</h2>
      <p>A new user has registered and is awaiting your approval:</p>
      <table style="border-collapse: collapse; width: 100%;">
        <tr><td style="padding: 8px; font-weight: bold;">Username</td><td style="padding: 8px;">{username}</td></tr>
        <tr><td style="padding: 8px; font-weight: bold;">Email</td><td style="padding: 8px;">{user_email}</td></tr>
      </table>
      <br>
      <a href="{approve_url}" style="background:#1da1f2;color:white;padding:12px 24px;text-decoration:none;border-radius:4px;margin-right:12px;display:inline-block;">
        ✅ Approve User
      </a>
      <a href="{reject_url}" style="background:#e0245e;color:white;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">
        ❌ Reject User
      </a>
      <br><br>
      <p style="color:#888;font-size:12px;">F&amp;O Trader Admin System</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[F&O Trader] New user approval required: {username}"
    msg["From"] = settings.gmail_sender
    msg["To"] = settings.admin_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.gmail_sender, settings.gmail_app_password)
        server.sendmail(settings.gmail_sender, settings.admin_email, msg.as_string())
