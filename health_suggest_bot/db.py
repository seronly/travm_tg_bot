from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, engine, User, Question
import datetime
import os
import logging


Base.metadata.create_all(engine)
Session = scoped_session(sessionmaker(engine))


# User
def create_user(update) -> None:
    """Сохраняет пользователя в базу данных, если его еще нет

    Args:
        update (Update): Ответ бота
    """
    session = Session()
    user = update.effective_user
    if not get_user(user.id):
        is_admin = str(user.id) in os.getenv("ADMIN_IDS").split(", ")
        user_db = User(
            tg_id=user.id,
            fullname=user.full_name,
            username=user.username,
            first_start=datetime.datetime.now(),
            is_admin=is_admin,
        )
        logging.info(f"Added user {User}")
        session.add(user_db)
        session.commit()


def get_user(user_id: int) -> User | None:
    """Получение пользователя с бд

    Args:
        user_id (int): ID пользователя

    Returns:
        User | None: Возвращает пользователя,
        если он есть в бд или None, если нет
    """
    session = Session()
    result = session.query(User).filter_by(tg_id=user_id).first()
    return result


def get_user_list(with_admin: bool) -> list[User]:
    session = Session()
    if with_admin:
        result = session.query(User).all()
    else:
        result = session.query(User).filter_by(is_admin=False)
    return result


def is_admin(user_id: int) -> bool:
    return get_user(user_id).is_admin


# Question
def save_question(question: Question) -> Question:
    session = Session()
    question = session.add(question)
    session.commit()
    return question


def get_question(question_id) -> Question:
    session = Session()
    question = (
        session.query(Question).filter_by(question_id=question_id).first()
    )
    return question


def delete_question(question: Question):
    session = Session()
    session.delete(question)
