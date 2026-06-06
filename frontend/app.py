import streamlit as st
from components.utils import login, logout, make_api_call
from components.review_queue import show_review_queue
from components.browse import show_browse
from components.statements import show_statements
from components.category_rules import show_category_rules
from config import ENDPOINTS

st.set_page_config(page_title="Household Finance Copilot", layout="wide")

st.markdown("""
<style>
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0.35rem 0.6rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] > div {
    gap: 0.25rem !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Review Queue"


def show_login():
    """Display login form."""
    st.title("🏠 Household Finance Copilot")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Login")

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True):
            if username and password:
                success, message = login(username, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter username and password")


def show_main_app():
    """Display authenticated main app."""
    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        st.title("🏠 Household Finance Copilot")
    with col2:
        st.markdown(f"**Logged in as:** {st.session_state['username']}")
        if st.button("Logout", use_container_width=False):
            logout()
            st.rerun()

    st.markdown("---")

    # Default to Browse when no pending transactions
    token = st.session_state["auth_token"]
    ok, resp = make_api_call("GET", ENDPOINTS["pending_transactions"], token=token, params={"limit": 1})
    has_pending = ok and resp.get("total", 0) > 0

    if has_pending:
        tab_review, tab_browse, tab_statements, tab_rules = st.tabs(["Review Queue", "Browse", "Statements", "Rules"])
    else:
        tab_browse, tab_statements, tab_review, tab_rules = st.tabs(["Browse", "Statements", "Review Queue", "Rules"])

    with tab_review:
        show_review_queue(token)

    with tab_browse:
        show_browse(token)

    with tab_statements:
        show_statements(token)

    with tab_rules:
        show_category_rules(token)


# Main logic
if st.session_state["auth_token"]:
    show_main_app()
else:
    show_login()
