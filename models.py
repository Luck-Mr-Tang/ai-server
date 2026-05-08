from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    avatar: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(32), default="", index=True)
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    # role: 'super' (审核员) | 'user' (普通用户)
    role: Mapped[str] = mapped_column(String(16), default="user", index=True)
    # status: 'pending' | 'approved' | 'rejected' | 'disabled'
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    # 1 = 受保护账号（不可删除，例如内置 admin 测试号）
    is_protected: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AICharacter(Base):
    __tablename__ = "ai_characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    avatar: Mapped[str] = mapped_column(String(255), default="")
    tagline: Mapped[str] = mapped_column(String(255), default="")
    persona: Mapped[str] = mapped_column(Text)
    is_builtin: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("ai_characters.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Moment(Base):
    __tablename__ = "moments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("ai_characters.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    character: Mapped["AICharacter"] = relationship("AICharacter")
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="moment", cascade="all, delete-orphan"
    )
    likes: Mapped[list["Like"]] = relationship(
        "Like", back_populates="moment", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    moment_id: Mapped[int] = mapped_column(ForeignKey("moments.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    moment: Mapped["Moment"] = relationship("Moment", back_populates="comments")
    user: Mapped["User"] = relationship("User")


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("moment_id", "user_id", name="uq_like_moment_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    moment_id: Mapped[int] = mapped_column(ForeignKey("moments.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    moment: Mapped["Moment"] = relationship("Moment", back_populates="likes")
