import socks
import socket
import threading
from urllib.parse import urlparse
from breeze_connect import BreezeConnect
from app.config import settings

_client: BreezeConnect | None = None
_lock = threading.Lock()


def _configure_proxy():
    """Route traffic through QuotaGuard static IP proxy."""
    if not settings.quotaguard_url:
        return
    parsed = urlparse(settings.quotaguard_url)
    socks.set_default_proxy(
        socks.SOCKS5,
        parsed.hostname,
        parsed.port,
        username=parsed.username,
        password=parsed.password,
    )
    socket.socket = socks.socksocket


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
