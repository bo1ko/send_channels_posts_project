import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import logging

logger = logging.getLogger(__name__)

def send_email(subject: str, body: str, to_email: str, from_email: str, smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str, image_path: str = None):
    """
    Sends an email with the specified text and, if needed, an image as an attachment.

    :param subject: The subject of the email
    :param body: The body of the email
    :param to_email: The recipient's email address
    :param from_email: The sender's email address
    :param smtp_server: The SMTP server address
    :param smtp_port: The SMTP server port
    :param smtp_user: The username for the SMTP server
    :param smtp_password: The password for the SMTP server
    :param image_path: The path to the image for the attachment (optional)
    """

    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add the email body
        msg.attach(MIMEText(body, 'html'))
     
        # If an image path is provided, add it as an attachment
        if image_path and os.path.isfile(image_path):
            with open(image_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(image_path)}',
                )
                msg.attach(part)

        # Connect to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            logger.info('Message sent.')

            return True

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
