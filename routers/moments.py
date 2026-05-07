from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ai_service import ai
from deps import get_current_user, get_db
from models import AICharacter, Comment, Like, Moment, User
from schemas import CommentIn, CommentOut, GenerateMomentIn, MomentOut

router = APIRouter(prefix="/api/moments", tags=["moments"])


def _serialize(m: Moment, user_id: int, db: Session) -> MomentOut:
    like_count = db.query(func.count(Like.id)).filter(Like.moment_id == m.id).scalar() or 0
    comment_count = db.query(func.count(Comment.id)).filter(Comment.moment_id == m.id).scalar() or 0
    liked = (
        db.query(Like.id).filter(Like.moment_id == m.id, Like.user_id == user_id).first() is not None
    )
    return MomentOut(
        id=m.id,
        content=m.content,
        image_url=m.image_url,
        created_at=m.created_at,
        character=m.character,
        like_count=like_count,
        comment_count=comment_count,
        liked_by_me=liked,
    )


@router.get("", response_model=list[MomentOut])
def feed(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 20,
):
    rows = db.query(Moment).order_by(Moment.created_at.desc()).limit(limit).all()
    return [_serialize(m, user.id, db) for m in rows]


@router.post("/generate", response_model=MomentOut)
async def generate(
    payload: GenerateMomentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    character = db.get(AICharacter, payload.character_id)
    if not character:
        raise HTTPException(404, "character not found")
    topic_hint = f"主题提示：{payload.topic}。" if payload.topic else ""
    prompt = (
        f"以 {character.name} 的视角发一条朋友圈动态。"
        f"人设：{character.persona}。{topic_hint}"
        "要求：60～120 字，第一人称，像真人随手发的，可适度使用 emoji，不要加引号或前缀。"
    )
    text = await ai.chat([{"role": "user", "content": prompt}], temperature=0.95)

    m = Moment(character_id=character.id, content=text)
    db.add(m)
    db.commit()
    db.refresh(m)
    return _serialize(m, user.id, db)


@router.post("/{moment_id}/like")
def toggle_like(
    moment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.get(Moment, moment_id):
        raise HTTPException(404, "moment not found")
    existing = (
        db.query(Like).filter(Like.moment_id == moment_id, Like.user_id == user.id).first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"liked": False}
    db.add(Like(moment_id=moment_id, user_id=user.id))
    db.commit()
    return {"liked": True}


@router.get("/{moment_id}/comments", response_model=list[CommentOut])
def list_comments(moment_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Comment)
        .filter(Comment.moment_id == moment_id)
        .order_by(Comment.id.asc())
        .all()
    )


@router.post("/{moment_id}/comments", response_model=CommentOut)
async def add_comment(
    moment_id: int,
    payload: CommentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    moment = db.get(Moment, moment_id)
    if not moment:
        raise HTTPException(404, "moment not found")

    c = Comment(moment_id=moment_id, user_id=user.id, content=payload.content)
    db.add(c)
    db.commit()
    db.refresh(c)

    character = db.get(AICharacter, moment.character_id)
    if character:
        prompt = (
            f"你是 {character.name}，刚发了一条动态：「{moment.content}」。"
            f"用户 {user.username} 评论：「{payload.content}」。"
            f"用人设语气回一条评论，30 字以内，自然口语。人设：{character.persona}"
        )
        reply = await ai.chat([{"role": "user", "content": prompt}], temperature=0.9)
        ai_user = db.query(User).filter(User.username == f"__ai__{character.id}").first()
        if not ai_user:
            ai_user = User(username=f"__ai__{character.id}", avatar=character.avatar)
            db.add(ai_user)
            db.commit()
            db.refresh(ai_user)
        db.add(Comment(moment_id=moment_id, user_id=ai_user.id, content=reply))
        db.commit()

    db.refresh(c)
    return c
