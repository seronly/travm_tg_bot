from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    BigInteger,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    tg_id = Column(BigInteger, unique=True, primary_key=True)
    fullname = Column(String(130))
    username = Column(String(35))
    first_start = Column(DateTime(True))
    is_admin = Column(Boolean(False))
    is_blocked = Column(Boolean(False))

    def __init__(
        self,
        tg_id: int,
        fullname: str,
        username: str,
        first_start,
        is_admin: bool,
        is_blocked: bool,
    ) -> None:
        self.tg_id = tg_id
        self.fullname = fullname
        self.username = username
        self.first_start = first_start
        self.is_admin = is_admin
        self.is_blocked = is_blocked

    def __repr__(self) -> str:
        return (
            f"<User(id={self.tg_id!r}, "
            f"username={self.username!r}, "
            f"first_start={self.first_start!r}, "
            f"is_admin={self.is_admin!r}, "
            f"is_blocked={self.is_blocked!r})>"
        )


class Question(Base):
    __tablename__ = "questions"
    question_id = Column(BigInteger, unique=True, primary_key=True)
    owner_id = Column(BigInteger, ForeignKey("users.tg_id"))
    attachment_path = Column(String(255))
    text = Column(String(255))

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
