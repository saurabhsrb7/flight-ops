import smtplib
import structlog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = structlog.get_logger()

# Email configuration (for production, use environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")

def send_email_notification(email_content: dict):
    """
    Send email notification
    email_content should contain: to_email, subject, body
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = email_content['to_email']
        msg['Subject'] = email_content['subject']
        
        # Add body to email
        msg.attach(MIMEText(email_content['body'], 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        # Login to the server
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, email_content['to_email'], text)
        server.quit()
        
        logger.info(
            "Email sent successfully",
            to_email=email_content['to_email'],
            subject=email_content['subject']
        )
        
    except Exception as e:
        logger.error(
            "Failed to send email",
            to_email=email_content['to_email'],
            error=str(e)
        )
        # In a real application, you might want to raise the exception
        # or handle it differently based on your requirements
        raise e

def send_mock_email_notification(email_content: dict):
    """
    Mock email notification for development/testing
    """
    logger.info(
        "Mock email notification",
        to_email=email_content['to_email'],
        subject=email_content['subject'],
        body=email_content['body'][:100] + "..."  # Truncate for logging
    )
    
    # In development, we'll just log the email instead of actually sending it
    return True 