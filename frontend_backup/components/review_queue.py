import base64
import streamlit as st
from typing import Optional
from components.utils import (
    make_api_call,
    format_currency,
    format_confidence,
    format_date,
    get_transaction_document,
    show_tag_section,
    put_tags,
)
from config import ENDPOINTS, PAGE_SIZE

OWNERS = ["—", "Rafael", "Heloisa", "Shared"]
CATEGORIES = [
    "—", "Groceries", "Restaurants", "Transportation", "Utilities",
    "Shopping", "Entertainment", "Healthcare", "Travel",
    "Insurance", "Salary", "Bonus", "Investments", "Other",
]


def show_review_queue(token: str):
    """Display review queue tab with pending transactions and side document panel."""

    if "page_num" not in st.session_state:
        st.session_state["page_num"] = 1
    if "sort_order" not in st.session_state:
        st.session_state["sort_order"] = "date_desc"
    if "selected_tx_id" not in st.session_state:
        st.session_state["selected_tx_id"] = None

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        if st.button("🔄 Check for new emails", use_container_width=True):
            poll_emails(token)
    with col2:
        sort_options = {
            "Date (newest first)": "date_desc",
            "Date (oldest first)": "date_asc",
            "Amount (high to low)": "amount_desc",
            "Amount (low to high)": "amount_asc",
            "Confidence (high to low)": "confidence_desc",
        }
        selected_sort = st.selectbox(
            "Sort by:",
            list(sort_options.keys()),
            index=0,
            key="sort_select",
            label_visibility="collapsed",
        )
        st.session_state["sort_order"] = sort_options[selected_sort]

    st.markdown("---")

    success, response = fetch_pending_transactions(
        token, st.session_state["page_num"], st.session_state["sort_order"]
    )
    if not success:
        st.error(response)
        return

    transactions = response.get("transactions", [])
    total_count = response.get("total", 0)
    total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)

    if not transactions:
        st.info("✓ No pending transactions! You're all caught up.")
        return

    col_list, col_doc = st.columns([1, 1])

    with col_list:
        display_transactions(token, transactions)

        st.markdown("---")
        p1, p2, p3 = st.columns(3)
        with p1:
            if st.session_state["page_num"] > 1:
                if st.button("← Previous"):
                    st.session_state["page_num"] -= 1
                    st.rerun()
        with p2:
            st.write(
                f"Page {st.session_state['page_num']} of {total_pages} "
                f"({total_count} total)"
            )
        with p3:
            if st.session_state["page_num"] < total_pages:
                if st.button("Next →"):
                    st.session_state["page_num"] += 1
                    st.rerun()

    with col_doc:
        show_document_panel(token)


def show_document_panel(token: str):
    st.subheader("Source Document")
    tx_id = st.session_state.get("selected_tx_id")
    if not tx_id:
        st.info("Click '📄' on a transaction to view its source document.")
        return

    with st.spinner("Loading document..."):
        doc = get_transaction_document(token, tx_id)

    if doc is None:
        st.warning("No document attached to this transaction.")
        return

    st.caption(f"**{doc['filename']}**  |  Uploaded: {doc.get('uploaded_at', '')[:10]}")
    file_bytes = base64.b64decode(doc["data"])
    st.download_button(
        "⬇ Download",
        data=file_bytes,
        file_name=doc["filename"],
        mime=doc["mime_type"],
        use_container_width=True,
    )

    mime = doc.get("mime_type", "")
    if mime.startswith("image/"):
        st.image(file_bytes, use_container_width=True)
    elif mime == "application/pdf":
        st.info("PDF preview not supported. Use the download button to open.")
    else:
        st.info(f"Preview not available for {mime}. Use the download button.")


def fetch_pending_transactions(token: str, page: int, sort_order: str) -> tuple[bool, dict]:
    sort_by, order = parse_sort_order(sort_order)
    return make_api_call(
        "GET",
        ENDPOINTS["pending_transactions"],
        token=token,
        params={"sort_by": sort_by, "sort_order": order, "page": page, "limit": PAGE_SIZE},
    )


def parse_sort_order(sort_order: str) -> tuple[str, str]:
    mapping = {
        "date_desc": ("date", "desc"),
        "date_asc": ("date", "asc"),
        "amount_desc": ("amount", "desc"),
        "amount_asc": ("amount", "asc"),
        "confidence_desc": ("confidence", "desc"),
    }
    return mapping.get(sort_order, ("date", "desc"))


def display_transactions(token: str, transactions: list):
    for tx in transactions:
        tx_id = tx["id"]
        with st.container(border=True):
            current_owner = tx.get("owner") or "—"
            current_category = tx.get("category") or "—"
            bank = tx.get("bank") or ""
            merchant = tx.get("merchant") or "—"

            c1, c2, c3, c_own, c_cat, c_app, c_rej, c_edit, c_doc = st.columns(
                [1.1, 0.9, 2.2, 1.3, 1.6, 0.9, 0.9, 0.45, 0.45]
            )
            with c1:
                st.markdown(f"**{format_date(tx['date'])}**")
            with c2:
                st.markdown(format_currency(tx["amount"]))
            with c3:
                st.markdown(f"**{merchant}**" + (f"  ·  *{bank}*" if bank else ""))
            with c_own:
                owner_val = st.selectbox(
                    "Owner", OWNERS,
                    index=OWNERS.index(current_owner) if current_owner in OWNERS else 0,
                    key=f"owner_{tx_id}", label_visibility="collapsed",
                )
            with c_cat:
                cat_val = st.selectbox(
                    "Category", CATEGORIES,
                    index=CATEGORIES.index(current_category) if current_category in CATEGORIES else 0,
                    key=f"cat_{tx_id}", label_visibility="collapsed",
                )
            with c_app:
                if st.button("✓", key=f"approve_{tx_id}", use_container_width=True):
                    save_and_approve(token, tx_id, owner_val, cat_val)
            with c_rej:
                if st.button("✗", key=f"reject_{tx_id}", use_container_width=True):
                    reject_transaction(token, tx_id)
            with c_edit:
                if st.button("✏️", key=f"edit_btn_{tx_id}", use_container_width=True):
                    k = f"editing_{tx_id}"
                    st.session_state[k] = not st.session_state.get(k, False)
                    st.rerun()
            with c_doc:
                is_selected = st.session_state.get("selected_tx_id") == tx_id
                if st.button("◀" if is_selected else "📄", key=f"doc_{tx_id}", use_container_width=True):
                    st.session_state["selected_tx_id"] = None if is_selected else tx_id
                    st.rerun()

            show_tag_section(token, tx_id, tx.get("tags", []), ENDPOINTS)

            if st.session_state.get(f"editing_{tx_id}", False):
                show_edit_form(token, tx)


def show_edit_form(token: str, tx: dict):
    tx_id = tx["id"]
    with st.form(key=f"edit_form_{tx_id}"):
        st.markdown("**Edit Transaction**")
        c1, c2 = st.columns(2)
        with c1:
            merchant = st.text_input("Merchant", value=tx.get("merchant", ""), key=f"e_merch_{tx_id}")
            amount = st.number_input("Amount", value=float(tx["amount"]), key=f"e_amt_{tx_id}")
        with c2:
            description = st.text_input("Description", value=tx.get("description") or "", key=f"e_desc_{tx_id}")
        if st.form_submit_button("Save"):
            update_transaction(token, tx_id, merchant=merchant, amount=amount, description=description)
    if st.button("Cancel", key=f"cancel_{tx_id}"):
        st.session_state[f"editing_{tx_id}"] = False
        st.rerun()


def save_and_approve(token: str, tx_id: str, owner: str, category: str):
    """Patch owner+category then approve."""
    data = {}
    if owner != "—":
        data["owner"] = owner
    if category != "—":
        data["category"] = category

    if data:
        make_api_call(
            "PATCH",
            f"{ENDPOINTS['update_transaction']}/{tx_id}",
            data=data,
            token=token,
        )

    success, response = make_api_call(
        "POST",
        f"{ENDPOINTS['approve_transaction']}/{tx_id}/approve",
        token=token,
    )
    if success:
        st.success("✓ Approved")
        st.rerun()
    else:
        st.error(f"Failed to approve: {response}")


def poll_emails(token: str):
    with st.spinner("Checking for new emails..."):
        success, response = make_api_call("POST", ENDPOINTS["poll_email"], token=token)
    if success:
        new_count = response.get("new_transactions", 0)
        if new_count > 0:
            st.success(f"✓ Found {new_count} new transaction(s)")
            st.session_state["page_num"] = 1
            st.rerun()
        else:
            st.info("No new transactions")
    else:
        st.error(f"Failed to check emails: {response}")


def update_transaction(token: str, tx_id: str, merchant: str, amount: float, description: str):
    success, response = make_api_call(
        "PATCH",
        f"{ENDPOINTS['update_transaction']}/{tx_id}",
        data={"merchant": merchant, "amount": amount, "description": description},
        token=token,
    )
    if success:
        st.success("✓ Updated")
        st.session_state[f"editing_{tx_id}"] = False
        st.rerun()
    else:
        st.error(f"Failed to update: {response}")


def reject_transaction(token: str, tx_id: str):
    success, response = make_api_call(
        "POST",
        f"{ENDPOINTS['reject_transaction']}/{tx_id}/reject",
        token=token,
    )
    if success:
        st.success("✓ Rejected")
        st.rerun()
    else:
        st.error(f"Failed to reject: {response}")
