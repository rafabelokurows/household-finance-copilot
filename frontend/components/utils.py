import requests
import streamlit as st
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any

from config import ENDPOINTS, API_TIMEOUT


def make_api_call(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    token: Optional[str] = None,
    params: Optional[Dict] = None,
) -> tuple[bool, Any]:
    """
    Make API call with error handling and auth token.
    Returns: (success: bool, response: dict or error message: str)
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method.upper() == "GET":
            resp = requests.get(
                endpoint, headers=headers, params=params, timeout=API_TIMEOUT
            )
        elif method.upper() == "POST":
            resp = requests.post(
                endpoint, json=data, headers=headers, timeout=API_TIMEOUT
            )
        elif method.upper() == "PATCH":
            resp = requests.patch(
                endpoint, json=data, headers=headers, timeout=API_TIMEOUT
            )
        elif method.upper() == "PUT":
            resp = requests.put(
                endpoint, json=data, headers=headers, timeout=API_TIMEOUT
            )
        else:
            return False, "Unsupported HTTP method"

        # Handle 401 — token expired or invalid
        if resp.status_code == 401:
            st.session_state["auth_token"] = None
            st.session_state["username"] = None
            return False, "Session expired. Please log in again."

        # Handle other errors
        if resp.status_code >= 400:
            error_detail = resp.json().get("detail", resp.text)
            return False, f"Error {resp.status_code}: {error_detail}"

        return True, resp.json()

    except requests.Timeout:
        return False, "Connection timeout. Please try again."
    except requests.RequestException as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login with username/password.
    Returns: (success: bool, message: str)
    """
    success, response = make_api_call(
        "POST",
        ENDPOINTS["login"],
        data={"username": username, "password": password},
    )

    if success:
        st.session_state["auth_token"] = response.get("token")
        st.session_state["username"] = response.get("username")
        return True, "Login successful"
    else:
        return False, response


def logout():
    """Clear auth state."""
    token = st.session_state.get("auth_token")
    if token:
        make_api_call("POST", ENDPOINTS["logout"], token=token)
    st.session_state["auth_token"] = None
    st.session_state["username"] = None


def format_currency(amount: float) -> str:
    """Format number as USD currency."""
    return f"${amount:,.2f}"


def format_confidence(confidence: int) -> str:
    """Format confidence score with visual indicator."""
    if confidence < 60:
        return f"{confidence}% 🔶"
    elif confidence < 80:
        return f"{confidence}%"
    else:
        return f"{confidence}% ✓"


def show_tag_section(token: str, tx_id: str, current_tags: list, endpoints: dict):
    """Inline tag chips + add input. Pass ENDPOINTS dict from config."""
    tag_cols = st.columns([4, 1])
    with tag_cols[0]:
        if current_tags:
            cols = st.columns(min(len(current_tags), 6))
            for i, tag in enumerate(current_tags):
                with cols[i % len(cols)]:
                    if st.button(f"× {tag}", key=f"rmtag_{tx_id}_{tag}", use_container_width=True):
                        put_tags(token, tx_id, [t for t in current_tags if t != tag], endpoints)
        else:
            st.caption("no tags")
    with tag_cols[1]:
        new_tag = st.text_input(
            "tag",
            key=f"tag_input_{tx_id}",
            label_visibility="collapsed",
            placeholder="add tag…",
        )
        if st.button("＋", key=f"tag_add_{tx_id}", use_container_width=True) and new_tag.strip():
            put_tags(token, tx_id, current_tags + [new_tag.strip().lower()], endpoints)


def put_tags(token: str, tx_id: str, tags: list, endpoints: dict):
    success, response = make_api_call(
        "PUT",
        f"{endpoints['transaction_tags']}/{tx_id}/tags",
        data={"tags": tags},
        token=token,
    )
    if success:
        st.rerun()
    else:
        st.error(f"Failed to update tags: {response}")


def get_transaction_document(token: str, tx_id: str):
    """Fetch document for a transaction. Returns doc dict or None."""
    success, response = make_api_call(
        "GET", f"{ENDPOINTS['transactions']}/{tx_id}/document", token=token
    )
    return response if success else None


def format_date(date_str: str) -> str:
    """Format ISO date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str
