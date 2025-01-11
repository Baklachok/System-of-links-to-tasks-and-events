from celery import Celery
from celery.schedules import crontab

# Создаём приложение Celery
celery = Celery(
    "app",  # Название приложения
    broker="amqp://guest:guest@rabbitmq:5672/",  # RabbitMQ брокер
    backend="rpc://",  # Бэкенд для сохранения результатов (по умолчанию RPC)
)

# Опциональные настройки Celery
celery.conf.beat_schedule = {
    "send-task-reminder-every-60-minutes": {
        "task": "app.tasks.notifications.send_task_reminder",  # Имя задачи
        "schedule": crontab(minute="*/60"),  # Каждые 60 минут
    },
}

celery.conf.task_default_queue = "default"
celery.conf.result_backend = "rpc://"
celery.conf.accept_content = ["json"]
celery.conf.task_serializer = "json"
celery.autodiscover_tasks(['app.tasks.notifications'])
