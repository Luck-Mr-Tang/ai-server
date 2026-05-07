from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    if not x_user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing X-User-Id header")
    user = db.get(User, x_user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user
