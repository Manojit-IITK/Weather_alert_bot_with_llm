import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logger import logger
from config import EMAIL_USER, EMAIL_PASSWORD, ALERT_RECIPIENT

def send_email_alert(subject, body):
    """
    Sends an email alert using Gmail SMTP.
    If EMAIL_USER or EMAIL_PASSWORD is not set, falls back to logging the alert.
    """
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.info("=" * 60)
        logger.info("[ALERT NOT SENT - EMAIL CREDENTIALS MISSING IN .env]")
        logger.info(f"SUBJECT: {subject}")
        logger.info(f"BODY:\n{body}")
        logger.info("=" * 60)
        return True

    try:
        # Create message container
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = ALERT_RECIPIENT or EMAIL_USER
        msg["Subject"] = subject
        
        # Attach body
        msg.attach(MIMEText(body, "plain"))
        
        # Connect to Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Secure the connection
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Send mail
        server.sendmail(EMAIL_USER, msg["To"], msg.as_string())
        server.quit()
        
        logger.info(f"Email alert successfully sent to {msg['To']} for subject: '{subject}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        # Log it as a fallback
        logger.info("=" * 60)
        logger.info(f"[FALLBACK LOG - EMAIL SEND FAILED] SUBJECT: {subject}")
        logger.info(f"BODY:\n{body}")
        logger.info("=" * 60)
        return False
