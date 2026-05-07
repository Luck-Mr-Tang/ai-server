import logging

import httpx

from config import settings

log = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(self) -> None:
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.model = settings.deepseek_model
        self.api_key = settings.deepseek_api_key

    async def chat(self, messages: list[dict], temperature: float = 0.8) -> str:
        if not self.api_key:
            return "[未配置 DEEPSEEK_API_KEY，这是一条占位回复。]"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            except httpx.HTTPStatusError as exc:
                log.error("DeepSeek HTTP %s: %s", exc.response.status_code, exc.response.text)
                return f"[AI 服务出错：{exc.response.status_code}]"
            except Exception as exc:  # noqa: BLE001
                log.exception("DeepSeek call failed")
                return f"[AI 服务异常：{exc}]"


ai = DeepSeekClient()
