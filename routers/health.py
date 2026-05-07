import time

from fastapi import APIRouter

from ai_service import ai
from config import settings
from redis_client import cache

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health():
    return {"status": "ok"}


@router.get("/ai")
async def health_ai():
    """Ping DeepSeek with a 1-token prompt to verify key + network."""
    if not settings.deepseek_api_key:
        return {"ok": False, "reason": "DEEPSEEK_API_KEY 未配置"}
    started = time.perf_counter()
    reply = await ai.chat([{"role": "user", "content": "ping"}], temperature=0.1)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    ok = not reply.startswith("[")  # error replies are wrapped in [ ... ]
    return {
        "ok": ok,
        "model": settings.deepseek_model,
        "latency_ms": elapsed_ms,
        "sample": reply[:80],
    }


@router.get("/redis")
def health_redis():
    fallback = type(cache).__name__ == "_MemoryFallback"
    try:
        cache.set("__healthcheck__", "1", ex=10)
        ok = cache.get("__healthcheck__") == "1"
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "fallback": fallback, "reason": str(exc)}
    return {"ok": ok, "fallback": fallback}
