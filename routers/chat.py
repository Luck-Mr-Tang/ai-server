import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_service import ai
from deps import get_current_user, get_db
from models import AICharacter, ChatMessage, User
from redis_client import cache
from schemas import ChatIn, ChatMessageOut

router = APIRouter(prefix="/api/chat", tags=["chat"])

CONTEXT_TURNS = 10


def _ctx_key(user_id: int, character_id: int) -> str:
    return f"chat:ctx:{user_id}:{character_id}"


def _load_context(user_id: int, character_id: int) -> list[dict]:
    raw = cache.get(_ctx_key(user_id, character_id))
    return json.loads(raw) if raw else []


def _save_context(user_id: int, character_id: int, msgs: list[dict]) -> None:
    cache.set(_ctx_key(user_id, character_id), json.dumps(msgs[-CONTEXT_TURNS * 2 :]), ex=3600 * 6)


@router.get("/{character_id}/history", response_model=list[ChatMessageOut])
def history(
    character_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id, ChatMessage.character_id == character_id)
        .order_by(ChatMessage.id.asc())
        .limit(100)
        .all()
    )


@router.post("/{character_id}", response_model=list[ChatMessageOut])
async def send(
    character_id: int,
    payload: ChatIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    character = db.get(AICharacter, character_id)
    if not character:
        raise HTTPException(404, "character not found")

    user_msg = ChatMessage(
        user_id=user.id, character_id=character_id, role="user", content=payload.content
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    ctx = _load_context(user.id, character_id)
    ctx.append({"role": "user", "content": payload.content})

    messages = [
        {"role": "system", "content": f"你是 {character.name}。{character.persona} 用中文回复，控制在 200 字以内，符合人设语气。"},
        *ctx,
    ]
    reply_text = await ai.chat(messages)

    ai_msg = ChatMessage(
        user_id=user.id, character_id=character_id, role="assistant", content=reply_text
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    ctx.append({"role": "assistant", "content": reply_text})
    _save_context(user.id, character_id, ctx)

    return [user_msg, ai_msg]
