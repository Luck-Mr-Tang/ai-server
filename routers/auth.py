from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from deps import get_current_user, get_db
from models import User
from schemas import RegisterIn, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), limit: int = 50):
    """List existing users (excluding AI shadow users prefixed with __ai__)."""
    rows = (
        db.query(User)
        .filter(~User.username.like("__ai__%"))
        .order_by(User.id.desc())
        .limit(limit)
        .all()
    )
    return rows


@router.post("/register-or-login", response_model=UserOut)
def register_or_login(payload: RegisterIn, db: Session = Depends(get_db)):
    """Auto-create user if username doesn't exist; otherwise return existing.

    MVP shortcut: no password. Frontend stores returned id and sends X-User-Id.
    """
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        user = User(username=payload.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
