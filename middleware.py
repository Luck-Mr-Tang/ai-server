import json

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class EnvelopeMiddleware(BaseHTTPMiddleware):
    """Wraps every JSON response in {code, success, data, msg}.

    Skips:
      - non-JSON responses (HTML, files, etc.)
      - paths starting with /docs, /openapi.json, /redoc (Swagger needs raw spec)
    """

    SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json")

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in self.SKIP_PREFIXES):
            return await call_next(request)

        response = await call_next(request)
        ctype = response.headers.get("content-type", "")
        if not ctype.startswith("application/json"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body) if body else None
        except json.JSONDecodeError:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=ctype,
            )

        ok = 200 <= response.status_code < 300
        if ok:
            envelope = {"code": response.status_code, "success": True, "data": data, "msg": "ok"}
        else:
            msg = "error"
            if isinstance(data, dict):
                detail = data.get("detail")
                if isinstance(detail, str):
                    msg = detail
                elif isinstance(detail, list) and detail:
                    first = detail[0]
                    msg = first.get("msg", "validation error") if isinstance(first, dict) else str(first)
                elif detail is not None:
                    msg = str(detail)
            envelope = {"code": response.status_code, "success": False, "data": None, "msg": msg}

        return JSONResponse(envelope, status_code=response.status_code)
