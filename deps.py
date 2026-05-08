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
    if user.status != "approved":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"account not active: {user.status}")
    return user


def get_super_user(user: User = Depends(get_current_user)) -> User:
    if user.role != "super":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "super role required")
    return user
