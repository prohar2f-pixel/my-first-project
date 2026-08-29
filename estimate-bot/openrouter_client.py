import os
from urllib.parse import urlsplit


def require_loopback_http_proxy() -> str:
    value = os.getenv("OPENROUTER_HTTP_PROXY", "")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(
            "OPENROUTER_HTTP_PROXY must be an HTTP proxy on 127.0.0.1 with an explicit port"
        )
    return value


def create_async_client(client_factory=None):
    proxy = require_loopback_http_proxy()
    if client_factory is None:
        import httpx

        client_factory = httpx.AsyncClient
    return client_factory(proxy=proxy)
