import streamlit as st
from components.utils import login, logout
from components.review_queue import show_review_queue
from components.browse import show_browse

st.set_page_config(page_title="Household Finance Copilot", layout="wide")

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

    # Tabs
    tab1, tab2 = st.tabs(["Review Queue", "Browse"])

    with tab1:
        show_review_queue(st.session_state["auth_token"])

    with tab2:
        show_browse(st.session_state["auth_token"])


# Main logic
if st.session_state["auth_token"]:
    show_main_app()
else:
    show_login()
