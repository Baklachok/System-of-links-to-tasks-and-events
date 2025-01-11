import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import getenv

from app.core.logger import logger
from app.models.task import Task


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


def send_task_email_notification(task: Task):
    user = task.user
    if not user or not user.email:
        logger.warning(f"Email пользователя отсутствует для задачи ID {task.id}")
        return

    subject = f"Напоминание о задаче: {task.title}"
    body = (
        f"Здравствуйте! Напоминаем вам о задаче:\n\n"
        f"Название: {task.title}\n"
        f"Описание: {task.description or 'Без описания'}\n\n"
        f"Задача ещё не выполнена. Пожалуйста, завершите её!\n"
    )

    try:
        logger.info(f"Отправка email на {user.email} для задачи ID {task.id}")
        send_email(user.email, subject, body)
    except Exception as e:
        logger.error(f"Ошибка отправки email для задачи ID {task.id}: {e}")
