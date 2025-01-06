import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import getenv

from app.core.logger import logger


def send_email(to_email: str, subject: str, body: str):
    """
    Отправка email с использованием SMTP.
    """
    smtp_server = getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(getenv("SMTP_PORT", 587))
    sender_email = getenv("SMTP_EMAIL")
    sender_password = getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:
        logger.error("Email или пароль SMTP не указаны в переменных окружения.")
        return

    try:
        # Настраиваем сообщение
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Подключаемся к серверу
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())

        logger.info(f"Email успешно отправлен на {to_email}")
    except Exception as e:
        logger.error(f"Ошибка при отправке email: {e}")
