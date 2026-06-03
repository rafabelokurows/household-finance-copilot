import base64
import streamlit as st
from typing import Optional
from components.utils import (
    make_api_call,
    format_currency,
    format_confidence,
    format_date,
    get_transaction_document,
)
from config import ENDPOINTS, PAGE_SIZE


def show_review_queue(token: str):
    """Display review queue tab with pending transactions and side document panel."""

    # Initialize session state
    if "page_num" not in st.session_state:
        st.session_state["page_num"] = 1
    if "sort_order" not in st.session_state:
        st.session_state["sort_order"] = "date_desc"
    if "selected_tx_id" not in st.session_state:
        st.session_state["selected_tx_id"] = None

    # Toolbar row
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

    # Fetch pending transactions
    success, response = fetch_pending_transactions(
        token, st.session_state["page_num"], st.session_state["sort_order"]
    )
    if not success:
        st.error(response)
        return

    transactions = response.get("transactions", [])
    total_count = response.get("total", 0)
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE

    if not transactions:
        st.info("✓ No pending transactions! You're all caught up.")
        return

    # Side-panel layout: list left, document right
    col_list, col_doc = st.columns([1, 1])

    with col_list:
        display_transactions(token, transactions)

        st.markdown("---")

        # Pagination
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
    """Render source document panel on right side of review queue."""
    st.subheader("Source Document")

    tx_id = st.session_state.get("selected_tx_id")
    if not tx_id:
        st.info("Click '📄 Source' on a transaction to view its source document.")
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


def fetch_pending_transactions(
    token: str, page: int, sort_order: str
) -> tuple[bool, dict]:
    """Fetch pending transactions from backend."""
    sort_by, order = parse_sort_order(sort_order)

    success, response = make_api_call(
        "GET",
        ENDPOINTS["pending_transactions"],
        token=token,
        params={
            "sort_by": sort_by,
            "sort_order": order,
            "page": page,
            "limit": PAGE_SIZE,
        },
    )

    return success, response


def parse_sort_order(sort_order: str) -> tuple[str, str]:
    """Convert UI sort string to API params."""
    mapping = {
        "date_desc": ("date", "desc"),
        "date_asc": ("date", "asc"),
        "amount_desc": ("amount", "desc"),
        "amount_asc": ("amount", "asc"),
        "confidence_desc": ("confidence", "desc"),
    }
    return mapping.get(sort_order, ("date", "desc"))


def display_transactions(token: str, transactions: list):
    """Display transactions as interactive table with edit/approve/reject."""

    for idx, tx in enumerate(transactions):
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])

            with col1:
                st.write(f"**{format_date(tx['date'])}**")
            with col2:
                st.write(f"{format_currency(tx['amount'])}")
            with col3:
                st.write(format_confidence(tx.get("confidence", 0)))
            with col4:
                st.write(tx.get("category") or "—")
            with col5:
                st.write(tx.get("merchant") or "—")

            st.write(f"Description: {tx.get('description', '—')}")

            # Action buttons
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                if st.button("✏️ Edit", key=f"edit_{tx['id']}"):
                    st.session_state[f"edit_{tx['id']}"] = True

            with col_b:
                if st.button("✓ Approve", key=f"approve_{tx['id']}"):
                    approve_transaction(token, tx["id"])

            with col_c:
                if st.button("✗ Reject", key=f"reject_{tx['id']}"):
                    reject_transaction(token, tx["id"])

            with col_d:
                label = "📄 Source" if st.session_state.get("selected_tx_id") != tx["id"] else "◀ Close"
                if st.button(label, key=f"doc_{tx['id']}"):
                    if st.session_state.get("selected_tx_id") == tx["id"]:
                        st.session_state["selected_tx_id"] = None
                    else:
                        st.session_state["selected_tx_id"] = tx["id"]
                    st.rerun()

            # Edit form (inline)
            if st.session_state.get(f"edit_{tx['id']}", False):
                show_edit_form(token, tx)


def show_edit_form(token: str, tx: dict):
    """Display inline edit form for transaction."""
    st.write("**Edit Transaction**")

    col1, col2 = st.columns(2)
    with col1:
        category = st.text_input(
            "Category", value=tx.get("category", ""), key=f"cat_{tx['id']}"
        )
        amount = st.number_input(
            "Amount", value=tx["amount"], key=f"amt_{tx['id']}"
        )

    with col2:
        merchant = st.text_input(
            "Merchant", value=tx.get("merchant", ""), key=f"merch_{tx['id']}"
        )
        description = st.text_input(
            "Description",
            value=tx.get("description", ""),
            key=f"desc_{tx['id']}",
        )

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Save", key=f"save_{tx['id']}"):
            update_transaction(
                token,
                tx["id"],
                category=category,
                merchant=merchant,
                amount=amount,
                description=description,
            )

    with col_cancel:
        if st.button("Cancel", key=f"cancel_{tx['id']}"):
            st.session_state[f"edit_{tx['id']}"] = False
            st.rerun()


def poll_emails(token: str):
    """Poll for new emails."""
    with st.spinner("Checking for new emails..."):
        success, response = make_api_call(
            "POST", ENDPOINTS["poll_email"], token=token
        )

    if success:
        new_count = response.get("new_transactions", 0)
        if new_count > 0:
            st.success(f"✓ Found {new_count} new transaction(s)")
            st.session_state["page_num"] = 1  # Reset to first page
            st.rerun()
        else:
            st.info("No new transactions")
    else:
        st.error(f"Failed to check emails: {response}")


def update_transaction(
    token: str, tx_id: int, category: str, merchant: str, amount: float, description: str
):
    """Update transaction."""
    success, response = make_api_call(
        "PATCH",
        f"{ENDPOINTS['update_transaction']}/{tx_id}",
        data={
            "category": category,
            "merchant": merchant,
            "amount": amount,
            "description": description,
        },
        token=token,
    )

    if success:
        st.success("✓ Transaction updated")
        st.session_state[f"edit_{tx_id}"] = False
        st.rerun()
    else:
        st.error(f"Failed to update: {response}")


def approve_transaction(token: str, tx_id: int):
    """Approve transaction."""
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


def reject_transaction(token: str, tx_id: int):
    """Reject transaction."""
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
