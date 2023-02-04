from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import os
import dotenv
import custom_logging as cl
import bot

dotenv.load_dotenv()

logger = cl.logger


def main():
    application = Application.builder().token(os.getenv("API_TOKEN")).build()

    # User command
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help))
    # Send question
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot.send_text)
    )
    application.add_handler(MessageHandler(filters.PHOTO, bot.send_img))
    application.add_handler(MessageHandler(filters.VIDEO, bot.send_video))

    # Admin
    application.add_handler(CommandHandler("admin", bot.admin))
    application.add_handler(CommandHandler("send_ad", bot.send_ad))
    application.add_handler(CommandHandler("stats", bot.get_stats))

    application.add_handler(CallbackQueryHandler(bot.callback_handler))

    # Err handler
    application.add_error_handler(bot.error_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
