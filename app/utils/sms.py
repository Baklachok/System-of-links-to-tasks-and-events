import requests
from app.core.logger import logger
import os

SMSRU_API_KEY = os.getenv("SMSRU_API_KEY")  # Токен для доступа к SMS.ru API
SMSRU_API_URL = "https://sms.ru/sms/send"


def send_sms_notification(phone_number: str, message: str):
    """
    Отправляет SMS-уведомление с использованием SMS.ru.

    :param phone_number: Номер получателя (в формате +79123456789).
    :param message: Текст сообщения.
    """
    try:
        logger.info(f"Отправка SMS на {phone_number} через SMS.ru.")

        # Параметры запроса
        payload = {
            "api_id": SMSRU_API_KEY,
            "to": phone_number,
            "msg": message,
            "json": 1,  # Формат ответа - JSON
        }

        # Отправка запроса
        response = requests.post(SMSRU_API_URL, data=payload)
        response_data = response.json()

        if response_data.get("status") == "OK":
            sms_status = response_data.get("sms", {}).get(phone_number, {})
            if sms_status.get("status") == "OK":
                logger.info(f"SMS успешно отправлено на {phone_number}. ID сообщения: {sms_status.get('sms_id')}")
            else:
                logger.error(f"Ошибка отправки SMS на {phone_number}: {sms_status.get('status_text')}")
        else:
            logger.error(f"Ошибка отправки SMS через SMS.ru: {response_data.get('status_text')}")
    except Exception as e:
        logger.error(f"Ошибка при отправке SMS на {phone_number}: {e}")
