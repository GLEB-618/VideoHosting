from typing import Annotated
from datetime import datetime
from sqlalchemy import BigInteger, Text, Boolean, text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

from data.database import Base

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
# usid = Annotated[int, mapped_column(BigInteger, unique=True)]
stx = Annotated[str, mapped_column(Text)]


class Videos(Base):
    __tablename__ = "videos"

    id: Mapped[intpk]
    uid: Mapped[stx]
    title: Mapped[stx]
    description: Mapped[stx]
    likes: Mapped[int] = mapped_column(server_default=text("0"))
    dislikes: Mapped[int] = mapped_column(server_default=text("0"))
    approved: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))


class Users(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    login: Mapped[stx] = mapped_column(primary_key=True)
    password: Mapped[stx]


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[intpk]
    login: Mapped[stx] = mapped_column(primary_key=True)
    password: Mapped[stx]

class Comments(Base):
    __tablename__ = "comments"

    id: Mapped[intpk]
    username: Mapped[stx]
    uid: Mapped[stx]
    content: Mapped[stx]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    
# class Admins(Base):
#     __tablename__ = "admins"

#     id: Mapped[intpk]
#     user_id: Mapped[usid]
#     position: Mapped[int] = mapped_column(server_default=text("0"))

# class DQ(Base):
#     __tablename__ = "download_queue"

#     id: Mapped[intpk]
#     file_id: Mapped[stx]
#     text: Mapped[str] = mapped_column(Text, nullable=True)
#     active: Mapped[bool] = mapped_column(Boolean, server_default="false")

# class Photos(Base):
#     __tablename__ = "photos"

#     id: Mapped[intpk]
#     file_id: Mapped[stx]
#     type: Mapped[stx] = mapped_column(server_default="sfw")
#     name: Mapped[stx] = mapped_column(server_default="noname")
#     physical: Mapped[stx] = mapped_column(server_default="none")