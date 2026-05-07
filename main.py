import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from middleware import EnvelopeMiddleware
from routers import auth, characters, chat, health, moments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="AI Companion API", version="0.1.0")

app.add_middleware(EnvelopeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "AI Companion API is up.", "docs": "/docs"}


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(characters.router)
app.include_router(chat.router)
app.include_router(moments.router)
