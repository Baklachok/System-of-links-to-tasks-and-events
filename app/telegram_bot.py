from telegram.ext import ApplicationBuilder, CommandHandler
from app.core.db import SessionLocal
from app.models.user import User
from app.models.task import Task
from app.services.auth import save_telegram_chat_id
import os


async def start(update, context):
    """
    Обработчик команды /start.
    """
    db = SessionLocal()
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Ошибка: укажите ваш user_id. Пример: /start <user_id>")
            return

        user_id = args[0]
        chat_id = update.effective_chat.id

        # Сохраняем Telegram Chat ID пользователя
        save_telegram_chat_id(db, user_id, chat_id)
        await update.message.reply_text("Ваш Telegram Chat ID успешно сохранён!")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")
    finally:
        db.close()


def main():
    """
    Запуск Telegram-бота.
    """
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env!")

    # Создание приложения бота
    application = ApplicationBuilder().token(telegram_token).build()

    # Добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()
