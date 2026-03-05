"""
market_widget.py — reusable market data lookup widget.

Usage (any page):
    from components.market_widget import render_market_widget
    render_market_widget(key="my_page_widget")

The `key` parameter namespaces all session-state so multiple instances
on different pages never collide.
"""

from datetime import datetime

import streamlit as st
from components.api_client import api_post

_EXCHANGES = ["NSE", "BSE", "NFO", "BFO"]
_INSTRUMENTS = ["Equity (Cash)", "Options", "Futures"]
_PRODUCT_MAP = {
    "Equity (Cash)": "cash",
    "Options": "options",
    "Futures": "futures",
}
_RIGHT_OPTIONS = ["call", "put"]


def _k(key: str, field: str) -> str:
    """Namespace a session-state / widget key."""
    return f"mw_{key}_{field}"


def _card_css() -> str:
    return """
    <style>
      .mw-card {
        background: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 14px;
        padding: 16px 18px 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        font-family: Arial, sans-serif;
      }
      .mw-header {
        font-size: 13px;
        font-weight: 700;
        color: #657786;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        margin-bottom: 6px;
      }
      .mw-symbol {
        font-size: 18px;
        font-weight: 700;
        color: #14171a;
      }
      .mw-ltp {
        font-size: 28px;
        font-weight: 800;
        color: #14171a;
        margin: 4px 0 2px;
      }
      .mw-change-up   { color: #17bf63; font-size: 14px; font-weight: 600; }
      .mw-change-down { color: #e0245e; font-size: 14px; font-weight: 600; }
      .mw-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 4px 12px;
        margin-top: 10px;
        font-size: 13px;
        color: #657786;
      }
      .mw-grid span { color: #14171a; font-weight: 600; }
      .mw-ts {
        font-size: 11px;
        color: #aab8c2;
        margin-top: 10px;
        text-align: right;
      }
      .mw-error {
        background: #fff5f5;
        border: 1px solid #fed7d7;
        border-radius: 10px;
        padding: 10px 14px;
        color: #c53030;
        font-size: 13px;
      }
    </style>
    """


def _fmt(v, prefix="₹") -> str:
    if v is None:
        return "—"
    return f"{prefix}{v:,.2f}"


def _fmt_int(v) -> str:
    if v is None:
        return "—"
    return f"{v:,}"


def render_market_widget(key: str = "default") -> None:
    """Render the market data widget. `key` must be unique per page instance."""
    st.markdown(_card_css(), unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:13px;font-weight:700;color:#657786;'
        'letter-spacing:0.6px;text-transform:uppercase;margin-bottom:4px;">'
        "📡 Market Quote</p>",
        unsafe_allow_html=True,
    )

    # ── Form inputs ──────────────────────────────────────────────────────────
    symbol = st.text_input(
        "Symbol",
        key=_k(key, "symbol"),
        placeholder="e.g. NIFTY, RELIANCE",
    )

    col_ex, col_inst = st.columns(2)
    with col_ex:
        exchange = st.selectbox("Exchange", _EXCHANGES, key=_k(key, "exchange"))
    with col_inst:
        instrument = st.selectbox("Instrument", _INSTRUMENTS, key=_k(key, "instrument"))

    is_derivative = instrument in ("Options", "Futures")

    if is_derivative:
        expiry = st.text_input(
            "Expiry date",
            key=_k(key, "expiry"),
            placeholder="YYYY-MM-DDT07:00:00.000Z",
        )
    else:
        expiry = ""

    if instrument == "Options":
        col_r, col_sp = st.columns(2)
        with col_r:
            right = st.selectbox("Right", _RIGHT_OPTIONS, key=_k(key, "right"))
        with col_sp:
            strike = st.number_input(
                "Strike", min_value=0.0, step=50.0, key=_k(key, "strike")
            )
    else:
        right = ""
        strike = 0.0

    fetch = st.button("Fetch", key=_k(key, "fetch"), use_container_width=True, type="primary")

    # ── Fetch logic ──────────────────────────────────────────────────────────
    data_key = _k(key, "last_data")
    err_key = _k(key, "last_error")
    ts_key = _k(key, "last_ts")

    if fetch:
        if not symbol:
            st.warning("Enter a symbol first.")
        else:
            payload = {
                "stock_code": symbol.upper().strip(),
                "exchange_code": exchange,
                "product_type": _PRODUCT_MAP[instrument],
                "expiry_date": expiry or None,
                "right": right or None,
                "strike_price": float(strike) if strike else None,
            }
            try:
                resp = api_post("/api/market/quote", json=payload)
                if resp.status_code == 200:
                    st.session_state[data_key] = resp.json()
                    st.session_state[err_key] = None
                    st.session_state[ts_key] = datetime.now().strftime("%H:%M:%S")
                else:
                    st.session_state[data_key] = None
                    detail = resp.json().get("detail", "Failed to fetch quote.")
                    st.session_state[err_key] = detail
            except Exception as exc:
                st.session_state[data_key] = None
                st.session_state[err_key] = f"Connection error: {exc}"

    # ── Display ──────────────────────────────────────────────────────────────
    error = st.session_state.get(err_key)
    data = st.session_state.get(data_key)

    if error:
        st.markdown(
            f'<div class="mw-error">⚠️ {error}</div>',
            unsafe_allow_html=True,
        )
    elif data:
        ltp = data.get("ltp")
        close = data.get("close")
        change_str = ""
        if ltp is not None and close is not None and close != 0:
            chg = ltp - close
            pct = (chg / close) * 100
            arrow = "▲" if chg >= 0 else "▼"
            css_cls = "mw-change-up" if chg >= 0 else "mw-change-down"
            change_str = (
                f'<span class="{css_cls}">{arrow} {abs(chg):,.2f} ({abs(pct):.2f}%)</span>'
            )

        oi_row = ""
        if data.get("open_interest") is not None:
            oi_row = f"<div>OI</div><div><span>{_fmt_int(data.get('open_interest'))}</span></div>"

        ts = st.session_state.get(ts_key, "")
        label = f"{data['stock_code']} · {data['exchange_code']}"

        st.markdown(
            f"""
            <div class="mw-card">
              <div class="mw-symbol">{label}</div>
              <div class="mw-ltp">{_fmt(ltp)}</div>
              {change_str}
              <div class="mw-grid">
                <div>Open</div>  <div><span>{_fmt(data.get('open'))}</span></div>
                <div>High</div>  <div><span>{_fmt(data.get('high'))}</span></div>
                <div>Low</div>   <div><span>{_fmt(data.get('low'))}</span></div>
                <div>Close</div> <div><span>{_fmt(data.get('close'))}</span></div>
                <div>Volume</div><div><span>{_fmt_int(data.get('volume'))}</span></div>
                {oi_row}
              </div>
              <div class="mw-ts">Updated {ts}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
