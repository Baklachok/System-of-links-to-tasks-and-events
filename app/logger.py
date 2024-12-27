import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
    ],
)

logger = logging.getLogger("global_logger")
