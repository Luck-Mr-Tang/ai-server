from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from deps import get_current_user, get_db
from models import User
from schemas import LoginIn, RegisterIn, UserOut
from security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    """注册新账号。账号默认 status='pending'，需超管审核。"""
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户名已被使用")
    if payload.phone and db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "手机号已被使用")
    user = User(
        username=payload.username,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="user",
        status="pending",
        is_protected=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    """账号密码登录。仅 status='approved' 才允许登录。"""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    if user.status == "pending":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "账号正在审核中，请耐心等待")
    if user.status == "rejected":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "账号未通过审核")
    if user.status == "disabled":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "账号已被禁用")
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
