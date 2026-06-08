"""
Notification delivery — email via SendGrid SMTP, SMS via Twilio.
Both channels fail silently so they never crash the main request.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# EMAIL
# ──────────────────────────────────────────────────────────────────────────────

def send_email_notification(recipient_email, subject, plain_message, html_message=None):
  
  
    if not recipient_email:
        logger.debug("send_email: no recipient address — skipped")
        return False

    api_key = getattr(settings, 'SENDGRID_API_KEY', '').strip()
    if not api_key:
        logger.warning("send_email: SENDGRID_API_KEY not configured — skipped")
        return False

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    if not from_email:
        logger.warning("send_email: DEFAULT_FROM_EMAIL not configured — skipped")
        return False

    try:
        import urllib.request
        import urllib.error
        import json

        # Build the SendGrid v3 mail/send payload
        payload = {
            "personalizations": [
                {
                    "to":      [{"email": recipient_email}],
                    "subject": subject,
                }
            ],
            "from": {"email": from_email, "name": "Adasu University ERMS"},
            "content": [
                {"type": "text/plain", "value": plain_message},
            ],
        }

    
        if html_message:
            payload["content"].append(
                {"type": "text/html", "value": html_message}
            )

        data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            url='https://api.sendgrid.com/v3/mail/send',
            data=data,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type':  'application/json',
            },
            method='POST',
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            # SendGrid returns 202 Accepted on success
            if response.status == 202:
                logger.info(
                    "Email sent  to=%s  subject=%s",
                    recipient_email, subject
                )
                return True
            else:
                logger.error(
                    "Email unexpected status=%s  to=%s",
                    response.status, recipient_email
                )
                return False

    except urllib.error.HTTPError as exc:
        # Read the error body so we can log exactly what SendGrid rejected
        error_body = ''
        try:
            error_body = exc.read().decode('utf-8')
        except Exception:
            pass
        logger.error(
            "Email HTTP error  status=%s  to=%s  body=%s",
            exc.code, recipient_email, error_body
        )
        return False

    except Exception as exc:
        logger.error(
            "Email FAILED  to=%s  subject=%s  error=%s",
            recipient_email, subject, exc
        )
        return False


def build_html_email(recipient_name, title, message):
    """
   
    return f""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin:0;padding:0;background:#F0F4F8;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F0F4F8;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:white;border-radius:12px;overflow:hidden;
                      box-shadow:0 2px 12px rgba(0,0,0,.08);max-width:600px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1B2B5A,#0D7377);
                       padding:32px 40px;text-align:center;">
              <div style="font-size:32px;margin-bottom:8px;">🎓</div>
              <h1 style="color:white;margin:0;font-size:22px;font-weight:800;
                         letter-spacing:.5px;">Adasu University ERMS</h1>
              <p style="color:rgba(255,255,255,.65);margin:4px 0 0;font-size:13px;">
                Examination Results Management System
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px;">
              <h2 style="color:#1B2B5A;font-size:18px;font-weight:700;
                         margin:0 0 16px;">{title}</h2>
              <p style="color:#4A5568;font-size:15px;line-height:1.7;margin:0 0 8px;">
                Dear {recipient_name},
              </p>
              <p style="color:#4A5568;font-size:15px;line-height:1.7;margin:0 0 24px;">
                {message.replace(chr(10), '<br/>')}
              </p>
              <a href="#"
                 style="display:inline-block;background:linear-gradient(135deg,#1B2B5A,#0D7377);
                        color:white;text-decoration:none;padding:12px 28px;
                        border-radius:8px;font-weight:700;font-size:14px;">
                Log In to ERMS Portal
              </a>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#F8FAFC;padding:20px 40px;
                       border-top:1px solid #E2E8F0;text-align:center;">
              <p style="color:#718096;font-size:12px;margin:0;line-height:1.6;">
                This is an automated message from the ERMS portal.<br/>
                Rev. Fr. Moses Orshio Adasu University, Makurdi, Benue State, Nigeria.<br/>
                Please do not reply to this email.
                For support: <a href="mailto:erms-support@adasu.edu.ng"
                                style="color:#0D7377;">erms-support@adasu.edu.ng</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────────────────────
# SMS
# ──────────────────────────────────────────────────────────────────────────────

def send_sms_notification(phone_number, message):
    """
    Send an SMS via Twilio.
    Silently skips if Twilio credentials are not configured.
    Phone number must include country code: +2348012345678
    """
    sid         = getattr(settings, 'TWILIO_ACCOUNT_SID',  '').strip()
    token       = getattr(settings, 'TWILIO_AUTH_TOKEN',   '').strip()
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '').strip()

    if not all([sid, token, from_number]):
        logger.debug("send_sms: Twilio not configured — skipped")
        return False

    if not phone_number:
        logger.debug("send_sms: no phone number — skipped")
        return False

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(
            body=message[:1600],
            from_=from_number,
            to=phone_number,
        )
        logger.info("SMS sent  to=%s", phone_number)
        return True
    except Exception as exc:
        logger.error("SMS FAILED  to=%s  error=%s", phone_number, exc)
        return False


# ──────────────────────────────────────────────────────────────────────────────
# COMBINED DISPATCHER — called by Notification.notify()
# ──────────────────────────────────────────────────────────────────────────────

def notify_user(user, subject, message, send_email=True, send_sms=True):
    """
    Deliver email and/or SMS to a user.
    Called automatically by Notification.notify() — you rarely need to
    call this directly.
    """
    if send_email and user.email:
        recipient_name = user.get_full_name() or user.username
        # Build a clean title from the subject (strip the 'ERMS — ' prefix for display)
        display_title = subject.replace('ERMS — ', '')
        html_body = build_html_email(recipient_name, display_title, message)
        send_email_notification(
            recipient_email=user.email,
            subject=subject,
            plain_message=message,
            html_message=html_body,
        )

    if send_sms and getattr(user, 'phone_number', '').strip():
        # Keep SMS concise — first 320 characters of the plain message
        sms_text = f"Adasu Univ ERMS: {message[:280]}"
        send_sms_notification(user.phone_number.strip(), sms_text)
