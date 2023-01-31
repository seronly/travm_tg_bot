from sqlalchemy import (
    create_engine,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import declarative_base
import os

Base = declarative_base()
engine = create_engine(
    f"sqlite://{os.getenv('DB_URL')}",
    echo=False,
)


class User(Base):
    __tablename__ = "users"

    tg_id = Column(Integer, unique=True, primary_key=True)
    fullname = Column(String(50))
    username = Column(String(30))
    first_start = Column(DateTime(True))
    is_admin = Column(Boolean(False))

    def __init__(
        self,
        tg_id: int,
        fullname: str,
        username: str,
        first_start,
        is_admin: bool,
    ) -> None:
        self.tg_id = tg_id
        self.fullname = fullname
        self.username = username
        self.first_start = first_start
        self.is_admin = is_admin

    def __repr__(self) -> str:
        return (
            f"<User(id={self.tg_id!r}, "
            f"username={self.username!r}, "
            f"first_start={self.first_start!r})"
            f"is_admin={self.is_admin!r})>"
        )


class Question(Base):
    __tablename__ = "questions"
    question_id = Column(Integer, unique=True, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.tg_id"))
    attachment_path = Column(String)
    text = Column(String)

    def __init__(self, owner_id, attachment_path, text):
        self.owner_id = owner_id
        self.attachment_path = attachment_path
        self.text = text

    def __repr__(self):
        return (
            f"<Question(question_id={self.question_id}, "
            f"owner_id={self.owner_id}, "
            f"attachment_filename={self.attachment_path}, text={self.text}>"
        )
