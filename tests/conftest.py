import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

def pytest_configure(config):
    log_level = os.getenv("PYTEST_LOG_LEVEL", "INFO")
    config.option.log_cli = True
    config.option.log_cli_level = log_level
