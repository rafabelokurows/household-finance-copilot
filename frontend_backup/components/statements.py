import streamlit as st
from components.utils import make_api_call, format_date
from config import ENDPOINTS


def show_statements(token: str):
    st.subheader("Bank Statements")

    success, response = make_api_call("GET", ENDPOINTS["statements"], token=token)
    if not success:
        st.error(f"Failed to load statements: {response}")
        return

    if not response:
        st.info("No statements ingested yet.")
        return

    for s in response:
        filename = s.get("filename") or "—"
        bank = s.get("bank") or "—"
        tx_count = s.get("tx_count", 0)
        period_start = s.get("period_start")
        period_end = s.get("period_end")
        processed_at = s.get("processed_at") or s.get("uploaded_at") or ""
        mime = s.get("mime_type") or ""

        if period_start and period_end and period_start != period_end:
            period = f"{format_date(period_start)} → {format_date(period_end)}"
        elif period_start:
            period = format_date(period_start)
        else:
            period = "—"

        processed_str = processed_at[:10] if processed_at else "—"
        icon = "🖼️" if mime.startswith("image/") else "📄"

        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([2.5, 1.5, 2, 1.5, 1])
            with c1:
                st.markdown(f"{icon} **{filename}**")
            with c2:
                st.markdown(f"🏦 {bank}")
            with c3:
                st.markdown(f"📅 {period}")
            with c4:
                st.markdown(f"⬆️ {processed_str}")
            with c5:
                st.markdown(f"**{tx_count}** txns")
