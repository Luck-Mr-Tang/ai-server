import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserOut(BaseModel):
    id: int
    username: str
    avatar: str
    role: str = "user"
    status: str = "approved"

    class Config:
        from_attributes = True


class AdminUserOut(BaseModel):
    id: int
    username: str
    phone: str
    avatar: str
    role: str
    status: str
    is_protected: int
    created_at: datetime

    class Config:
        from_attributes = True


_PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    phone: str = Field(min_length=11, max_length=11)
    password: str = Field(min_length=6, max_length=64)

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, v: str) -> str:
        if not _PHONE_RE.match(v):
            raise ValueError("手机号格式不正确，需 11 位且以 1 开头")
        return v


class LoginIn(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=1, max_length=64)


class CharacterIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    avatar: str = ""
    tagline: str = ""
    persona: str = Field(min_length=1)


class CharacterOut(BaseModel):
    id: int
    name: str
    avatar: str
    tagline: str
    persona: str
    is_builtin: int

    class Config:
        from_attributes = True


class ChatIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    user: UserOut

    class Config:
        from_attributes = True


class MomentOut(BaseModel):
    id: int
    content: str
    image_url: str
    created_at: datetime
    character: CharacterOut
    like_count: int
    comment_count: int
    liked_by_me: bool


class GenerateMomentIn(BaseModel):
    character_id: int
    topic: str = ""
