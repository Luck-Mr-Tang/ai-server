from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from deps import get_current_user, get_db
from models import AICharacter, User
from schemas import CharacterIn, CharacterOut

router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("", response_model=list[CharacterOut])
def list_characters(db: Session = Depends(get_db)):
    return db.query(AICharacter).order_by(AICharacter.is_builtin.desc(), AICharacter.id).all()


@router.get("/{cid}", response_model=CharacterOut)
def get_character(cid: int, db: Session = Depends(get_db)):
    c = db.get(AICharacter, cid)
    if not c:
        raise HTTPException(404, "character not found")
    return c


@router.post("", response_model=CharacterOut)
def create_character(
    payload: CharacterIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = AICharacter(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
