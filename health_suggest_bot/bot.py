from telegram import (
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)
from telegram.constants import ParseMode

import constants
from db import (
    create_user,
    get_user_list,
    is_admin,
    get_question,
    delete_question,
    save_question,
)
import json
import logging
from models import Question
import os


# Decorators
def admin_command(func):
    async def wrapper(*args, **kwargs):
        update, context = args
        if is_admin(update.effective_user.id):
            return await func(*args, **kwargs)
        else:
            return await update.message.reply_text("Отказано в доступе!")

    return wrapper


# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["current_question_index"] = 0
    text = constants.START_TEXT
    create_user(update)
    await update.message.reply_text(text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Для того, чтобы предложить пост, отправьте текст и/или изображение"
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())


async def send_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if str(update.effective_user.id) in os.getenv("ADMIN_IDS").split(","):
    #     return
    question = Question(update.effective_user.id, None, update.message.text)
    save_question(question)
    logging.info(f"New {question}")
    await context.bot.send_message(
        os.getenv("REPLY_USER_ID"),
        text=question.text + f"\n\nUser id: {question.owner_id}",
        reply_markup=InlineKeyboardMarkup(get_buttons(question)),
    )
    await update.message.reply_text(constants.THANKS_FOR_QUESTION)


async def send_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.photo[-1]
    photo = await file.get_file()
    question = Question(
        update.effective_user.id, photo.file_path, update.message.caption
    )
    save_question(question)

    logging.info(f"New {question}")
    await context.bot.send_photo(
        chat_id=os.getenv("REPLY_USER_ID"),
        photo=file,
        caption=(question.text if question.text else "")
        + f"\n\n User id: {question.owner_id}",
        reply_markup=InlineKeyboardMarkup(get_buttons(question)),
    )
    await update.message.reply_text(constants.THANKS_FOR_QUESTION)


async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.video
    print(file)
    video = await file.get_file()
    question = Question(
        update.effective_user.id, video.file_path, update.message.caption
    )
    save_question(question)
    logging.info(f"New {question}")
    await context.bot.send_video(
        chat_id=os.getenv("REPLY_USER_ID"),
        video=file,
        caption=(question.text if question.text else "")
        + f"\n\n User id: {question.owner_id}",
        reply_markup=InlineKeyboardMarkup(get_buttons(question)),
    )
    await update.message.reply_text(constants.THANKS_FOR_QUESTION)


def get_buttons(question: Question):
    return [
        [
            InlineKeyboardButton(
                "✅",
                callback_data=json.dumps(
                    {"question": question.question_id, "action": "accept"}
                ),
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=json.dumps(
                    {"question": question.question_id, "action": "decline"}
                ),
            ),
        ]
    ]


@admin_command
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="Чтобы отправить рассылку, введите "
        "/send_ad <i>текст сообщения</i>\n"
        "Вы так же можете вставить placeholders:\n"
        "{name} - полное имя человека в тг\n"
        "{username} - логин человека в тг\n",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


@admin_command
async def send_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_user_list(False)
    text = " ".join(update.message.text.split(" ")[1:])
    for user in users:
        await context.bot.send_message(
            user.tg_id,
            text=text.format(name=user.fullname, username=user.username),
            parse_mode=ParseMode.HTML,
        )
    await update.message.reply_text("Рассылка была отправлена!")


# Callbacks
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = json.loads(query.data)
    if is_admin(update.effective_user.id):
        question = get_question(data["question"])
        if question:
            if data["action"] == "accept":
                await query.answer(constants.SUCCESS_QUESTION_TEXT)
                # await context.bot.send_message(
                #     question.owner_id, "Ваш пост был опубликован!"
                # )
            elif data["action"] == "decline":
                await query.answer(constants.DECLINE_QUESTION_TEXT)
            await context.bot.delete_message(
                update.callback_query.message.chat_id,
                update.callback_query.message.message_id,
            )
            delete_question(question)
        else:
            logging.error(f"question with id {data['question']} not found")
            await query.answer(f"Вопрос с id {data['question']} не найден")

    else:
        logging.error(
            f"Unauthorized access detected!\nId: {update.effective_user.id}"
        )
        await query.answer("Отказано в доступе!")
