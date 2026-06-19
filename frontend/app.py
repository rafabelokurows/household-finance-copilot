import streamlit as st
from components.utils import login, logout, make_api_call
from components.review_queue import show_review_queue
from components.browse import show_browse
from components.statements import show_statements
from components.category_rules import show_category_rules
from config import ENDPOINTS

st.set_page_config(
    page_title="Finance Copilot",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = """
<style>
/* ── Base ─────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', system-ui, sans-serif;
}

#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #252525; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #C9924A; }

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0d0d0d !important;
    border-right: 1px solid #1c1c1c !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}
[data-testid="stSidebar"] section {
    padding-top: 0 !important;
}

/* Nav radio → nav links */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 2px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-radius: 6px !important;
    padding: 10px 14px !important;
    color: #6b6460 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(201,146,74,0.07) !important;
    color: #d8d3ca !important;
}
/* Hide radio circles */
[data-testid="stSidebar"] [data-baseweb="radio"] { display: none !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
}

/* ── Main content ─────────────────────────────────────────── */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px !important;
}

/* ── Cards ────────────────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #141414 !important;
    border-color: #1e1e1e !important;
    border-radius: 8px !important;
    transition: border-color 0.15s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #282828 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0.4rem 0.7rem !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] > div {
    gap: 0.2rem !important;
}

/* ── Buttons ──────────────────────────────────────────────── */
.stButton > button {
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    border: 1px solid #252525 !important;
    background: #181818 !important;
    color: #b8b3ac !important;
}
.stButton > button:hover {
    background: #202020 !important;
    border-color: #C9924A !important;
    color: #C9924A !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}
[data-testid="baseButton-primary"] {
    background: #C9924A !important;
    color: #0a0a0a !important;
    border-color: #C9924A !important;
    font-weight: 600 !important;
}
[data-testid="baseButton-primary"]:hover {
    background: #d4a05a !important;
    border-color: #d4a05a !important;
    color: #0a0a0a !important;
    transform: translateY(-1px) !important;
}

/* ── Inputs ───────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: #111 !important;
    border-color: #242424 !important;
    border-radius: 6px !important;
    color: #e4ddd3 !important;
    font-size: 13px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #C9924A !important;
    box-shadow: 0 0 0 2px rgba(201,146,74,0.12) !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #111 !important;
    border-color: #242424 !important;
    border-radius: 6px !important;
    color: #e4ddd3 !important;
    font-size: 13px !important;
}
[data-testid="stDateInput"] input {
    background: #111 !important;
    border-color: #242424 !important;
    border-radius: 6px !important;
    color: #e4ddd3 !important;
    font-size: 13px !important;
}

/* ── Metrics ──────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 8px;
    padding: 16px 20px;
}
[data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-variant-numeric: tabular-nums !important;
    color: #e4ddd3 !important;
}
[data-testid="stMetricLabel"] {
    color: #6b6460 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

/* ── Dividers ─────────────────────────────────────────────── */
hr { border-color: #1c1c1c !important; margin: 0.8rem 0 !important; }

/* ── Expanders ────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border-color: #1e1e1e !important;
    border-radius: 8px !important;
    background: #0f0f0f !important;
}
[data-testid="stExpander"] summary {
    color: #8a8480 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* ── Alerts ───────────────────────────────────────────────── */
[data-testid="stInfo"] {
    background: rgba(77,166,255,0.06) !important;
    border-left-color: #4da6ff !important;
    border-radius: 6px !important;
}
[data-testid="stSuccess"] {
    background: rgba(82,183,136,0.08) !important;
    border-left-color: #52b788 !important;
    border-radius: 6px !important;
}
[data-testid="stError"] {
    background: rgba(248,113,113,0.08) !important;
    border-left-color: #f87171 !important;
    border-radius: 6px !important;
}
[data-testid="stWarning"] {
    background: rgba(253,224,71,0.06) !important;
    border-left-color: #fde047 !important;
    border-radius: 6px !important;
}

/* ── Subheaders & captions ────────────────────────────────── */
h3 {
    color: #d8d3ca !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
}
[data-testid="stCaptionContainer"] p {
    color: #6b6460 !important;
    font-size: 11px !important;
}
</style>
"""

# ── Session state ─────────────────────────────────────────────────

if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

st.markdown(_CSS, unsafe_allow_html=True)


def show_login():
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown("""
        <div style="background:#141414;border:1px solid #1e1e1e;border-radius:12px;padding:40px 36px;margin-top:60px">
            <div style="font-size:22px;font-weight:700;color:#e4ddd3;letter-spacing:-0.02em;margin-bottom:4px">Finance Copilot</div>
            <div style="font-size:12px;color:#5a5450;margin-bottom:28px;text-transform:uppercase;letter-spacing:0.08em">Household tracker</div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", key="login_username", placeholder="your username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        if st.button("Sign in", use_container_width=True, type="primary"):
            if username and password:
                success, message = login(username, password)
                if success:
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Enter username and password")

        st.markdown("</div>", unsafe_allow_html=True)


def show_main_app():
    token = st.session_state["auth_token"]

    ok, resp = make_api_call("GET", ENDPOINTS["pending_transactions"], token=token, params={"limit": 1})
    pending_count = resp.get("total", 0) if ok else 0
    review_label = f"Review Queue  ({pending_count})" if pending_count else "Review Queue"

    nav_items = ["Browse", review_label, "Statements", "Rules"]

    with st.sidebar:
        st.markdown("""
        <div style="padding:24px 16px 18px;border-bottom:1px solid #1c1c1c;margin-bottom:12px">
            <div style="font-size:17px;font-weight:700;color:#e4ddd3;letter-spacing:-0.02em">Finance Copilot</div>
            <div style="font-size:10px;color:#4a4440;margin-top:3px;text-transform:uppercase;letter-spacing:0.1em">Household tracker</div>
        </div>
        """, unsafe_allow_html=True)

        page = st.radio("nav", nav_items, label_visibility="collapsed")

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="border-top:1px solid #1c1c1c;padding:14px 16px 6px">
            <div style="font-size:12px;color:#5a5450;margin-bottom:8px">{st.session_state['username']}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Sign out", use_container_width=True):
            logout()
            st.rerun()

    if page == "Browse":
        show_browse(token)
    elif page.startswith("Review Queue"):
        show_review_queue(token)
    elif page == "Statements":
        show_statements(token)
    elif page == "Rules":
        show_category_rules(token)


if st.session_state["auth_token"]:
    show_main_app()
else:
    show_login()
