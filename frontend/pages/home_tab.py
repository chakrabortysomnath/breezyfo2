import streamlit as st


def render_home_tab() -> None:
    """Home tab — Work In Progress landing screen."""
    st.markdown("<br><br>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            """
            <div style="text-align:center; padding: 48px 32px;
                        border: 1px solid #e1e8ed; border-radius: 16px;
                        background: #ffffff; box-shadow: 0 2px 12px rgba(0,0,0,0.06);">
                <div style="font-size:72px; margin-bottom:16px;">🚧</div>
                <h2 style="color:#14171a; font-size:26px; margin-bottom:8px;">
                    Work in Progress
                </h2>
                <p style="color:#657786; font-size:16px; line-height:1.6; margin-bottom:24px;">
                    Your personalised F&amp;O trading dashboard is being built.<br>
                    Check back soon for live P&amp;L, portfolio analytics, and more.
                </p>
                <div style="display:inline-block; background:#1da1f2; color:white;
                            padding:10px 24px; border-radius:24px; font-weight:600;
                            font-size:14px; letter-spacing:0.5px;">
                    📈 F&amp;O Trader
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        username = st.session_state.get("username", "Trader")
        st.markdown(
            f'<p style="text-align:center;color:#657786;font-size:13px;">'
            f"Welcome, <strong>{username}</strong>. Use the tabs above to get started."
            f"</p>",
            unsafe_allow_html=True,
        )
