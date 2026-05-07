import logging

import redis

from config import settings

log = logging.getLogger(__name__)


class _MemoryFallback:
    """Used when Redis isn't running. Lets you develop without installing Redis."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str):
        return self._store.get(key)

    def set(self, key: str, value: str, ex: int | None = None):
        self._store[key] = value

    def delete(self, key: str):
        self._store.pop(key, None)

    def incr(self, key: str) -> int:
        v = int(self._store.get(key, "0")) + 1
        self._store[key] = str(v)
        return v


def _build():
    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        log.info("Redis connected: %s", settings.redis_url)
        return client
    except Exception as exc:  # noqa: BLE001
        log.warning("Redis unavailable (%s). Falling back to in-memory store.", exc)
        return _MemoryFallback()


cache = _build()
