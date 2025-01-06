from celery import Celery

# Создаём приложение Celery
celery = Celery(
    "app",  # Название приложения
    broker="amqp://guest:guest@rabbitmq:5672/",  # RabbitMQ брокер
    backend="rpc://",  # Бэкенд для сохранения результатов (по умолчанию RPC)
)

# Опциональные настройки Celery
celery.conf.task_routes = {
    "app.tasks.*": {"queue": "default"},
}
celery.conf.task_default_queue = "default"
celery.conf.result_backend = "rpc://"
celery.conf.accept_content = ["json"]
celery.conf.task_serializer = "json"
celery.autodiscover_tasks(['app.tasks'])
