from __future__ import annotations
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

_DISABLED = os.getenv("RATE_LIMIT_DISABLED", "").lower() in ("1", "true", "yes")
_BACKEND = (os.getenv("RATE_LIMIT_BACKEND") or "").lower()
_REDIS_URL = os.getenv("REDIS_URL") or os.getenv("REDIS_URI")

if _DISABLED:
    class _NoopLimiter:
        def limit(self, *args, **kwargs):
            def _decorator(func):
                return func
            return _decorator

        def shared_limit(self, *args, **kwargs):
            return self.limit(*args, **kwargs)

    limiter = _NoopLimiter()  
    ENABLED = False
else:
    if _BACKEND == "redis" and _REDIS_URL:
        storage_uri = _REDIS_URL
    else:
        storage_uri = "memory://"

    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri,

    )
    ENABLED = True
