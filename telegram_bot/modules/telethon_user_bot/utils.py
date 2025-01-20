import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email(subject: str, body: str, to_email: str, from_email: str, smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str, image_path: str = None):
    """
    Надсилає електронний лист із заданим текстом та, за потреби, зображенням як вкладення.

    :param subject: Тема листа
    :param body: Текст листа
    :param to_email: Адреса отримувача
    :param from_email: Адреса відправника
    :param smtp_server: Адреса SMTP-сервера
    :param smtp_port: Порт SMTP-сервера
    :param smtp_user: Ім'я користувача для SMTP-сервера
    :param smtp_password: Пароль для SMTP-сервера
    :param image_path: Шлях до зображення для вкладення (необов'язково)
    """
    try:
        # Створюємо багаточастинне повідомлення
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Додаємо текст до повідомлення
        msg.attach(MIMEText(body, 'plain'))

        # Якщо вказано шлях до зображення, додаємо його як вкладення
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

        # Підключаємося до SMTP-сервера та надсилаємо лист
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            print('Лист успішно надіслано.')

    except Exception as e:
        print(f'Сталася помилка при надсиланні листа: {e}')
