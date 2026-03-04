import socks
import socket
from urllib.parse import urlparse
from breeze_connect import BreezeConnect
from app.config import settings


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
    _configure_proxy()
    breeze = BreezeConnect(api_key=settings.breeze_api_key)
    breeze.generate_session(
        api_secret=settings.breeze_api_secret,
        session_token=settings.breeze_session_token,
    )
    return breeze
