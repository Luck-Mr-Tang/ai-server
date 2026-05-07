from datetime import datetime

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    username: str
    avatar: str

    class Config:
        from_attributes = True


class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=32)


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
