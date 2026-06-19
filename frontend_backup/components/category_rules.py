import streamlit as st
from components.utils import make_api_call
from config import ENDPOINTS


def show_category_rules(token: str):
    st.subheader("Category Rules")
    st.caption("Keywords are matched case-insensitively against merchant names. First match wins.")

    success, rules = make_api_call("GET", ENDPOINTS["category_rules"], token=token)
    if not success:
        st.error(f"Failed to load rules: {rules}")
        return

    if not rules:
        st.info("No rules configured.")
        return

    for rule in rules:
        category = rule["category"]
        keywords = rule["keywords"]

        with st.expander(f"**{category}** — {len(keywords)} keyword(s)", expanded=False):
            # Display existing keywords as removable pills
            if keywords:
                cols = st.columns(min(len(keywords), 5))
                for i, kw in enumerate(keywords):
                    with cols[i % 5]:
                        if st.button(f"✕ {kw}", key=f"del_{category}_{kw}", use_container_width=True):
                            _delete_keyword(token, category, kw)
            else:
                st.caption("No keywords yet.")

            # Add new keyword
            c1, c2 = st.columns([4, 1])
            with c1:
                new_kw = st.text_input(
                    "New keyword", key=f"new_kw_{category}",
                    placeholder="e.g. some merchant name",
                    label_visibility="collapsed",
                )
            with c2:
                if st.button("Add", key=f"add_{category}", use_container_width=True):
                    if new_kw.strip():
                        _add_keyword(token, category, new_kw.strip())
                    else:
                        st.warning("Enter a keyword first")


def _add_keyword(token: str, category: str, keyword: str):
    success, response = make_api_call(
        "POST",
        f"{ENDPOINTS['category_rules']}/{category}/keywords",
        data={"keyword": keyword},
        token=token,
    )
    if success:
        st.success(f"Added '{keyword}' to {category}")
        st.rerun()
    else:
        st.error(f"Failed: {response}")


def _delete_keyword(token: str, category: str, keyword: str):
    success, response = make_api_call(
        "DELETE",
        f"{ENDPOINTS['category_rules']}/{category}/keywords/{keyword}",
        token=token,
    )
    if success:
        st.rerun()
    else:
        st.error(f"Failed to remove '{keyword}': {response}")
