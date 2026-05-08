import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from config import settings
from database import Base, SessionLocal, engine
from middleware import EnvelopeMiddleware
from models import User
from routers import admin, auth, characters, chat, health, moments
from security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("startup")

app = FastAPI(title="AI Companion API", version="0.1.0")

app.add_middleware(EnvelopeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 已有 SQLite 库需要补列时使用，避免重置数据
USER_COLUMN_PATCHES = {
    "phone": "VARCHAR(32) NOT NULL DEFAULT ''",
    "password_hash": "VARCHAR(255) NOT NULL DEFAULT ''",
    "role": "VARCHAR(16) NOT NULL DEFAULT 'user'",
    "status": "VARCHAR(16) NOT NULL DEFAULT 'approved'",
    "is_protected": "INTEGER NOT NULL DEFAULT 0",
}


def patch_user_columns() -> None:
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("users")}
    missing = {k: v for k, v in USER_COLUMN_PATCHES.items() if k not in existing}
    if not missing:
        return
    with engine.begin() as conn:
        for col, ddl in missing.items():
            log.info("patching users table: add column %s", col)
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ddl}"))


DEFAULT_USERS = [
    {
        "username": "super",
        "password": "x123456",
        "role": "super",
        "status": "approved",
        "is_protected": 1,
        "phone": "13800000000",
    },
    {
        "username": "admin",
        "password": "x123456",
        "role": "user",
        "status": "approved",
        "is_protected": 1,
        "phone": "13800000001",
    },
]


def seed_default_users() -> None:
    db = SessionLocal()
    try:
        for u in DEFAULT_USERS:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if existing:
                # 保持受保护标记 + 角色 + 已审核状态（管理员手滑改了也会被纠回）
                existing.is_protected = u["is_protected"]
                existing.role = u["role"]
                if existing.status not in ("approved",):
                    existing.status = u["status"]
                if not existing.password_hash:
                    existing.password_hash = hash_password(u["password"])
                continue
            db.add(
                User(
                    username=u["username"],
                    phone=u["phone"],
                    avatar="",
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                    status=u["status"],
                    is_protected=u["is_protected"],
                )
            )
        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    patch_user_columns()
    seed_default_users()


@app.get("/")
def root():
    return {"message": "AI Companion API is up.", "docs": "/docs"}


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(characters.router)
app.include_router(chat.router)
app.include_router(moments.router)
