import streamlit as st
from components.market_widget import render_market_widget


def render_home_tab() -> None:
    """Home tab — welcome content on the left, market widget on the right."""
    left, right = st.columns([2, 1], gap="large")

    with left:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="padding: 40px 32px;
                        border: 1px solid #e1e8ed; border-radius: 16px;
                        background: #ffffff; box-shadow: 0 2px 12px rgba(0,0,0,0.06);">
                <div style="font-size:64px; margin-bottom:12px;">🚧</div>
                <h2 style="color:#14171a; font-size:24px; margin-bottom:8px;">
                    Work in Progress
                </h2>
                <p style="color:#657786; font-size:15px; line-height:1.6; margin-bottom:20px;">
                    Your personalised F&amp;O trading dashboard is being built.<br>
                    Check back soon for live P&amp;L, portfolio analytics, and more.
                </p>
                <div style="display:inline-block; background:#1da1f2; color:white;
                            padding:8px 22px; border-radius:24px; font-weight:600;
                            font-size:13px; letter-spacing:0.5px;">
                    📈 F&amp;O Trader
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        username = st.session_state.get("username", "Trader")
        st.markdown(
            f'<p style="color:#657786;font-size:13px;">'
            f"Welcome, <strong>{username}</strong>. Use the tabs above to get started."
            f"</p>",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown("<br>", unsafe_allow_html=True)
        render_market_widget(key="home")
