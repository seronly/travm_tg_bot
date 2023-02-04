from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)
from telegram.constants import ParseMode
from telegram.error import Forbidden

import constants
import db
import json
import html
import custom_logging as cl
from models import Question
import os
import traceback

logger = cl.logger


# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = constants.START_TEXT
    db.create_or_update_user(update)
    await update.message.reply_text(text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Для того, чтобы задать вопрос, \
отправьте текст, изображение или видео"
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())


async def send_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = Question(update.effective_user.id, None, update.message.text)
    if len(question.text) > 250:
        await update.message.reply_text(constants.LONG_TEXT)
        return

    db.save_question(question)
    await context.bot.send_message(
        os.getenv("REPLY_USER_ID"),
        text=question.text + f"\n\nUser id: {question.owner_id}",
        reply_markup=InlineKeyboardMarkup(get_question_accept_btns(question)),
    )
    await update.message.reply_text(constants.THANKS_FOR_QUESTION)


async def send_img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.photo[-1]
    photo = await file.get_file()
    question = Question(
        update.effective_user.id, photo.file_path, update.message.caption
    )
    if len(question.text) > 250:
        await update.message.reply_text(constants.LONG_TEXT)
        return
    db.save_question(question)

    await context.bot.send_photo(
        chat_id=os.getenv("REPLY_USER_ID"),
        photo=file,
        caption=(question.text if question.text else "")
        + f"\n\n User id: {question.owner_id}",
        reply_markup=InlineKeyboardMarkup(get_question_accept_btns(question)),
    )
    await update.message.reply_text(constants.THANKS_FOR_QUESTION)


async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.video
    video = await file.get_file()
    question = Question(
        update.effective_user.id, video.file_path, update.message.caption
    )
    if len(question.text) > 250:
        await update.message.reply_text(constants.LONG_TEXT)
        return
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


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="/send_ad - Отправить рассылку\n"
        "/stats - получить статистику бота\n",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=constants.ADMIN_MENU_BTNS,
            resize_keyboard=True,
        ),
    )


async def start_send_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Да"], ["Нет"]]
    await update.message.reply_text(
        text="Нужно ли добавить текст рассылки?\n",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return constants.SEND_AD_TEXT


async def send_ad_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Да"], ["Нет"]]
    if update.message.text == "Да":
        await update.message.reply_text(
            "Отправьте текст", reply_markup=ReplyKeyboardRemove()
        )
        return constants.SEND_AD_TEXT
    elif update.message.text == "Нет":
        context.user_data["text"] = ""
    else:
        context.user_data["text"] = update.message.text
    await update.message.reply_text(
        "Нужно ли добавить фото или видео?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return constants.SEND_AD_ATTACHMENT


async def send_ad_attachment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.message.text == "Да":
        await update.message.reply_text(
            "Отправьте фото или видео.", reply_markup=ReplyKeyboardRemove()
        )
        return constants.SEND_AD_ATTACHMENT
    elif update.message.text == "Нет":
        ad_attachment_type = "text"
        ad_attachment = None
    elif update.message.photo:
        ad_attachment = update.message.photo[-1]
        ad_attachment_type = "photo"
    elif update.message.video:
        ad_attachment = update.message.video
        ad_attachment_type = "video"
    else:
        await update.message.reply_text(
            "Не потдерживаемый тип файла, "
            "отправьте другой или введите /cancel",
            reply_markup=ReplyKeyboardRemove(),
        )
        return constants.SEND_AD_ATTACHMENT
    post = {
        "text": context.user_data["text"],
        "attachment": ad_attachment,
        "type": ad_attachment_type,
    }
    context.user_data["post"] = post
    reply_keyboard = [["Да"], ["Нет"]]

    await update.message.reply_text(
        "Добавить кнопку к посту?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return constants.SEND_AD_BUTTON


async def send_ad_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Да":
        await update.message.reply_text(
            "Отправьте текст кнопки",
            reply_markup=ReplyKeyboardRemove(),
        )
        return constants.SEND_AD_BUTTON
    elif update.message.text == "Нет":
        await send_ad(update, context, context.user_data["post"])
        return ConversationHandler.END
    elif context.user_data["post"].get("button", None):
        context.user_data["post"]["button"] = {
            "text": context.user_data["post"]["button"]["text"],
            "url": update.message.text.strip(),
        }
        await send_ad(update, context, context.user_data["post"])
        return ConversationHandler.END
    else:
        context.user_data["post"]["button"] = {
            "text": update.message.text.strip()
        }
        await update.message.reply_text(
            "Введите ссылку",
        )
        return constants.SEND_AD_BUTTON


async def send_ad(
    update: Update, context: ContextTypes.DEFAULT_TYPE, post: dict
):
    if not post.get("text") and not post.get("attachment"):
        await update.message.reply_text(
            "Нет сообщения и/или изображения.\nРассылка не была отправлена.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=constants.ADMIN_MENU_BTNS,
                resize_keyboard=True,
            ),
        )
        return ConversationHandler.END
    users = db.get_all_users(inlcude_admin=False)
    sended_users_number = 0
    block_bot_users_number = 0
    text = post["text"]
    file = post["attachment"]
    button = (
        InlineKeyboardButton(
            text=post["button"]["text"],
            url=post["button"]["url"],
        )
        if post.get("button", None)
        else None
    )
    kb = InlineKeyboardMarkup([[button]]) if button else None

    try:
        for user in users:
            text = text.format(
                name=user.fullname or "Уважаемый пользователь",
                username=user.username or "",
            )
            if not user.is_blocked:
                if post["type"] == "photo":
                    await context.bot.send_photo(
                        chat_id=user.tg_id,
                        photo=file,
                        caption=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb,
                    )
                elif post["type"] == "video":
                    await context.bot.send_video(
                        chat_id=user.tg_id,
                        video=file,
                        caption=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb,
                    )
                else:
                    await context.bot.send_message(
                        user.tg_id,
                        text=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb,
                    )
                sended_users_number += 1
            else:
                block_bot_users_number += 1
    except Forbidden:
        db.update_user(user.tg_id, {"is_blocked": True})
        block_bot_users_number += 1
    finally:
        await update.message.reply_text(
            f"Рассылка была отправлена {sended_users_number} пользователям!\n"
            f"Пользователей, заблокировавших  бота: {block_bot_users_number}."
            f"\n\nПост:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=constants.ADMIN_MENU_BTNS,
                resize_keyboard=True,
            ),
        )
        if post["type"] == "photo":
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=file,
                caption=text.format(
                    name=user.fullname or "Уважаемый пользователь",
                    username=user.username or "",
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        elif post["type"] == "video":
            await context.bot.send_video(
                chat_id=update.effective_user.id,
                video=file,
                caption=text.format(
                    name=user.fullname or "Уважаемый пользователь",
                    username=user.username or "",
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=text.format(
                    name=user.fullname or "Уважаемый пользователь",
                    username=user.username or "",
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Создание рекламного поста завершено")
    return ConversationHandler.END


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


async def error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else,
    # so we can see it even if something breaks.
    logger.error(
        msg="Exception while handling an update:", exc_info=context.error
    )

    # traceback.format_exception returns the usual python message
    # about an exception,
    # but as a list of strings rather than a single string,
    # so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the message with some markup and
    # additional information about what happened.
    # You might need to add some logic to deal with messages
    # longer than the 4096 character limit.
    update_str = (
        update.to_dict() if isinstance(update, Update) else str(update)
    )
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = "
        f"{html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = "
        f"{html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = "
        f"{html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=os.getenv("DEVELOPER_CHAT_ID"),
        text=message,
        parse_mode=ParseMode.HTML,
    )


# Callbacks
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = json.loads(query.data)
    if db.is_admin(update.effective_user):
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
            logger.error(f"Question with id {data['question']} not found")
            await query.answer(f"Вопрос с id {data['question']} не найден")

    else:
        logger.error(
            f"Unauthorized access detected!\nId: {update.effective_user.id}"
        )
        await query.answer("Отказано в доступе!")
