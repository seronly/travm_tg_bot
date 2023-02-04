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
from telegram.error import Forbidden

import constants
import db
import json
import logging
from models import Question
import os


# Decorators
def admin_command(func):
    async def wrapper(*args, **kwargs):
        update, context = args
        if db.is_admin(update.effective_user.id):
            return await func(*args, **kwargs)
        else:
            return await update.message.reply_text("Отказано в доступе!")

    return wrapper


def user_command(func):
    async def wrapper(*args, **kwargs):
        update, context = args
        # user = get_user(update.effective_user.id)
        # uncommend if db broke again
        # if not user or not user.fullname:
        #     user = create_or_update_user(update)

        if not db.is_admin(update.effective_user.id):
            return await func(*args, **kwargs)

    return wrapper


# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["current_question_index"] = 0
    text = constants.START_TEXT
    db.create_or_update_user(update)
    await update.message.reply_text(text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Для того, чтобы задать вопрос, \
отправьте текст, изображение или видео"
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())


@user_command
async def send_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = Question(update.effective_user.id, None, update.message.text)
    db.save_question(question)
    await context.bot.send_message(
        os.getenv("REPLY_USER_ID"),
        text=question.text + f"\n\nUser id: {question.owner_id}",
        reply_markup=InlineKeyboardMarkup(get_question_accept_btns(question)),
    )
    await update.message.reply_text(constants.THANKS_FOR_QUESTION)


@user_command
async def send_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.photo[-1]
    photo = await file.get_file()
    question = Question(
        update.effective_user.id, photo.file_path, update.message.caption
    )
    db.save_question(question)

    await context.bot.send_photo(
        chat_id=os.getenv("REPLY_USER_ID"),
        photo=file,
        caption=(question.text if question.text else "")
        + f"\n\n User id: {question.owner_id}",
        reply_markup=InlineKeyboardMarkup(get_question_accept_btns(question)),
    )
    await update.message.reply_text(constants.THANKS_FOR_QUESTION)


@user_command
async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.video
    video = await file.get_file()
    question = Question(
        update.effective_user.id, video.file_path, update.message.caption
    )
    db.save_question(question)
    await context.bot.send_video(
        chat_id=os.getenv("REPLY_USER_ID"),
        video=file,
        caption=(question.text if question.text else "")
        + f"\n\n User id: {question.owner_id}",
        reply_markup=InlineKeyboardMarkup(get_question_accept_btns(question)),
    )
    await update.message.reply_text(constants.THANKS_FOR_QUESTION)


def get_question_accept_btns(question: Question):
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
        text="/send_ad <i>текст сообщения</i> - отправить рассылку\n"
        "Вы так же можете вставить placeholders:\n"
        "{name} - полное имя человека в тг\n"
        "{username} - логин человека в тг\n\n"
        "/stats - получить статистику бота\n",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


@admin_command
async def send_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_users(inlcude_admin=False)
    text = " ".join(update.message.text.split(" ")[1:])
    sended_users_number = 0
    block_bot_users_number = 0
    for user in users:
        try:
            if not user.is_blocked:
                await context.bot.send_message(
                    user.tg_id,
                    text=text.format(
                        name=user.fullname or "Уважаемый пользователь",
                        username=user.username or "",
                    ),
                    parse_mode=ParseMode.HTML,
                )
                sended_users_number += 1
            else:
                block_bot_users_number += 1
        except Forbidden:
            db.update_user(user.tg_id, {"is_blocked": True})
            block_bot_users_number += 1

    await update.message.reply_text(
        f"Рассылка была отправлена {sended_users_number} пользователям!\n"
        f"Пользователей, заблокировавших  бота: {block_bot_users_number}."
    )


@admin_command
async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_count = len(db.get_all_users(inlcude_admin=True))
    user_blocked = db.get_blocked_user_count()
    question_no_solved = db.get_question_count()

    text = (
        "Статистика:\n\n"
        f"Кол-во пользователей:\n👤 {user_count}\n"
        f"Кол-во пользователей, остановиших бота:\n🚫 {user_blocked}\n"
        f"Кол-во не отвеченных вопросов:\n❔ {question_no_solved}"
    )
    await update.message.reply_text(text)


# Callbacks
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = json.loads(query.data)
    if db.is_admin(update.effective_user.id):
        question = db.get_question(data["question"])
        if question:
            if data["action"] == "accept":
                await query.answer(constants.SUCCESS_QUESTION_TEXT)
                await context.bot.send_message(
                    question.owner_id, constants.USER_ACCEPTED_QUESTION
                )
            elif data["action"] == "decline":
                await query.answer(constants.DECLINE_QUESTION_TEXT)
            await context.bot.delete_message(
                update.callback_query.message.chat_id,
                update.callback_query.message.message_id,
            )
            db.delete_question(question)
        else:
            logging.error(f"Question with id {data['question']} not found")
            await query.answer(f"Вопрос с id {data['question']} не найден")

    else:
        logging.error(
            f"Unauthorized access detected!\nId: {update.effective_user.id}"
        )
        await query.answer("Отказано в доступе!")
