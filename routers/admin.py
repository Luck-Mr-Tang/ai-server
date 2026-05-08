from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from deps import get_db, get_super_user
from models import User
from schemas import AdminUserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserOut])
def list_all_users(
    status_filter: str | None = None,
    _: User = Depends(get_super_user),
    db: Session = Depends(get_db),
):
    """超管查看所有用户，可按 status 过滤（pending/approved/rejected/disabled）。"""
    q = db.query(User).filter(~User.username.like("__ai__%"))
    if status_filter:
        q = q.filter(User.status == status_filter)
    return q.order_by(User.created_at.desc()).all()


@router.post("/users/{uid}/approve", response_model=AdminUserOut)
def approve_user(
    uid: int,
    _: User = Depends(get_super_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    user.status = "approved"
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{uid}/reject", response_model=AdminUserOut)
def reject_user(
    uid: int,
    _: User = Depends(get_super_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if user.is_protected:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "受保护的账号不允许操作")
    user.status = "rejected"
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{uid}")
def delete_user(
    uid: int,
    current: User = Depends(get_super_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if user.is_protected:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "受保护的账号不允许删除")
    if user.id == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能删除自己")
    db.delete(user)
    db.commit()
    return {"deleted": uid}
