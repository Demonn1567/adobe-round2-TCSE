from __future__ import annotations
from typing import Iterable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class MaxBodyLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int, paths_prefixes: Optional[Iterable[str]] = None):
        super().__init__(app)
        self.max_body_size = int(max_body_size)
        self.paths_prefixes = tuple(paths_prefixes or ())

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            if self.paths_prefixes and not any(request.url.path.startswith(p) for p in self.paths_prefixes):
                return await call_next(request)
            cl = request.headers.get("content-length")
            if cl and cl.isdigit() and int(cl) > self.max_body_size:
                mb = self.max_body_size // (1024 * 1024)
                return JSONResponse({"detail": f"Payload too large. Limit is {mb} MB."}, status_code=413)
        return await call_next(request)
