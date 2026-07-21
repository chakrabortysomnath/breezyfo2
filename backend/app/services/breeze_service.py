import os
import threading
from urllib.parse import quote, urlsplit
from breeze_connect import BreezeConnect
from app.config import settings

_client: BreezeConnect | None = None
_lock = threading.Lock()


def _configure_proxy():
    """Route outbound Breeze traffic through the QuotaGuard static-IP proxy.

    breeze_connect performs all network calls with `requests`, which honours the
    HTTP_PROXY / HTTPS_PROXY environment variables (using PySocks automatically
    for a socks5:// URL).  We configure the proxy that way — honouring whatever
    scheme QUOTAGUARD_URL actually carries and URL-encoding the credentials —
    instead of forcing SOCKS5 and monkey-patching the socket module.  The old
    approach ignored the real proxy scheme and never authenticated through
    requests, producing "407 Proxy Authentication Required".
    """
    if not settings.quotaguard_url:
        return
    parts = urlsplit(settings.quotaguard_url)
    if not parts.hostname:
        return
    scheme = parts.scheme or "http"
    userinfo = ""
    if parts.username:
        userinfo = quote(parts.username, safe="")
        if parts.password:
            userinfo += ":" + quote(parts.password, safe="")
        userinfo += "@"
    port = f":{parts.port}" if parts.port else ""
    proxy_url = f"{scheme}://{userinfo}{parts.hostname}{port}"
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        os.environ[var] = proxy_url


def get_breeze_client() -> BreezeConnect:
    """Return the process-wide singleton Breeze client.

    generate_session() downloads the full security-master ZIP and validates
    the session token via an HTTP round-trip.  Calling it on every request
    causes severe latency and can exhaust rate limits.  We initialise it once
    and reuse across all requests.
    """
    global _client
    if _client is not None:
        return _client
    with _lock:
        if _client is None:          # double-checked locking
            _configure_proxy()
            client = BreezeConnect(api_key=settings.breeze_api_key)
            client.generate_session(
                api_secret=settings.breeze_api_secret,
                session_token=settings.breeze_session_token,
            )
            _client = client
    return _client


def reset_breeze_client() -> None:
    """Force re-initialisation of the client (call after session expiry)."""
    global _client
    with _lock:
        _client = None
