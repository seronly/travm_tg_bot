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
            is_blocked=False,
        )
        logging.info(f"Added user {User}")
        session.add(user_db)
    else:
        session.query(User).filter_by(tg_id=user.id).update(
            {"is_blocked": False}
        )
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


def get_user_list(inlcude_admin: bool = True) -> list[User]:
    session = Session()
    if inlcude_admin:
        result = session.query(User).all()
    else:
        result = session.query(User).filter_by(is_admin=False).all()
    return result


def get_user_list_wtih_block_status(
    blocked: bool, inlcude_admin: bool = True
) -> list[User]:
    session = Session()
    if inlcude_admin:
        result = session.query(User).filter_by(is_blocked=blocked).all()
    else:
        result = (
            session.query(User)
            .filter_by(is_admin=False, is_blocked=blocked)
            .all()
        )
    return result


def set_user_block_status(user_id: int, blocked: bool) -> None:
    session = Session()
    session.query(User).filter_by(tg_id=user_id).first().update(
        {"is_blocked": blocked}
    )
    session.commit()


def get_all_user_count() -> int:
    """Get number of all users

    Returns:
        int: number of users
    """
    session = Session()

    return len(session.query(User).all())


def get_blocked_user_count() -> int:
    """Get number of users who block bot

    Returns:
        int: number of users
    """
    session = Session()
    result = session.query(User).filter(User.is_blocked).all()
    return len(result)


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


def get_question_count() -> int:
    session = Session()
    return len(session.query(Question.question_id).all())


def delete_question(question: Question):
    session = Session()
    session.delete(question)
