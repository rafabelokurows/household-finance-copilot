import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from components.utils import make_api_call, format_currency, format_date, show_tag_section
from config import ENDPOINTS, CATEGORIES


def show_browse(token: str):
    """Display browse/analytics tab."""

    # Initialize session state
    if "date_from" not in st.session_state:
        st.session_state["date_from"] = datetime.now() - timedelta(weeks=12)
    if "date_to" not in st.session_state:
        st.session_state["date_to"] = datetime.now()
    if "category_filter" not in st.session_state:
        st.session_state["category_filter"] = "All"

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        date_from = st.date_input(
            "From:",
            value=st.session_state["date_from"],
            key="browse_from",
        )
        st.session_state["date_from"] = date_from

    with col2:
        date_to = st.date_input(
            "To:",
            value=st.session_state["date_to"],
            key="browse_to",
        )
        st.session_state["date_to"] = date_to

    with col3:
        category = st.selectbox(
            "Category:",
            ["All"] + CATEGORIES,
            index=0,
            key="browse_category",
        )
        st.session_state["category_filter"] = category

    export_col = st.columns(1)[0]
    with export_col:
        if st.button("📥 Export as CSV", use_container_width=False):
            export_csv(token, date_from, date_to)

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Spending by Category")
        show_category_chart(token, date_from, date_to)

    with col2:
        st.subheader("Spending Trends (12 weeks)")
        show_trends_chart(token)

    st.markdown("---")

    st.subheader("Spending by Tag")
    show_tag_chart(token, date_from, date_to)

    st.markdown("---")

    with st.expander("📅 Monthly Spending", expanded=False):
        show_monthly_chart(token)

    with st.expander("👤 Spending by Owner", expanded=False):
        show_owner_chart(token, date_from, date_to)

    with st.expander("📊 Category Trends (month-over-month)", expanded=False):
        show_category_trends_chart(token)

    st.markdown("---")

    # Transaction table
    st.subheader("Transactions")
    show_transaction_table(token, date_from, date_to, category)


def show_category_chart(token: str, date_from, date_to):
    """Display pie chart of spending by category."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["analytics_by_category"],
        token=token,
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
    )

    if not success:
        st.error(f"Failed to load chart: {response}")
        return

    categories = response.get("categories", [])

    if not categories:
        st.info("No data for this period")
        return

    cat_names = [c["name"] for c in categories]
    cat_amounts = [c["amount"] for c in categories]

    fig = go.Figure(
        data=[go.Pie(labels=cat_names, values=cat_amounts, textinfo="label+percent")]
    )
    fig.update_layout(height=400)

    st.plotly_chart(fig, use_container_width=True)


def show_trends_chart(token: str):
    """Display line chart of spending trends."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["analytics_trends"],
        token=token,
        params={"weeks": 12},
    )

    if not success:
        st.error(f"Failed to load chart: {response}")
        return

    weeks = response.get("weeks", [])

    if not weeks:
        st.info("No data for this period")
        return

    week_labels = [w["week_start"] for w in weeks]
    week_amounts = [w["total_spending"] for w in weeks]

    fig = go.Figure(
        data=[go.Scatter(x=week_labels, y=week_amounts, mode="lines+markers")]
    )
    fig.update_layout(
        title="",
        xaxis_title="Week",
        yaxis_title="Total Spending ($)",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_tag_chart(token: str, date_from, date_to):
    """Horizontal bar chart of spending per tag."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["analytics_by_tag"],
        token=token,
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
    )

    if not success:
        st.error(f"Failed to load tag data: {response}")
        return

    tag_data = response.get("tags", [])

    if not tag_data:
        st.info("No tagged transactions for this period")
        return

    names = [t["name"] for t in tag_data]
    amounts = [t["amount"] for t in tag_data]

    fig = go.Figure(
        data=[go.Bar(x=amounts, y=names, orientation="h", text=[f"€{a:,.2f}" for a in amounts], textposition="outside")]
    )
    fig.update_layout(
        height=max(200, len(names) * 40),
        xaxis_title="Total (€)",
        yaxis={"autorange": "reversed"},
        margin={"l": 0, "r": 80, "t": 10, "b": 40},
    )
    st.plotly_chart(fig, use_container_width=True)


def show_transaction_table(token: str, date_from, date_to, category_filter: str):
    """Display processed transactions as interactive cards."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["processed_transactions"],
        token=token,
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "sort_by": "date",
            "sort_order": "desc",
        },
    )

    if not success:
        st.error(f"Failed to load transactions: {response}")
        return

    transactions = response.get("transactions", [])

    if category_filter != "All":
        transactions = [tx for tx in transactions if tx.get("category") == category_filter]

    if not transactions:
        st.info("No transactions found for this period")
        return

    for tx in transactions:
        tx_id = tx["id"]
        with st.container(border=True):
            bank = tx.get("bank") or ""
            merchant = tx.get("merchant") or "—"
            c1, c2, c3, c4, c5 = st.columns([1, 0.9, 0.9, 0.9, 3.2])
            with c1:
                st.markdown(f"**{format_date(tx['date'])}**")
            with c2:
                st.markdown(format_currency(tx["amount"]))
            with c3:
                st.markdown(tx.get("owner") or "—")
            with c4:
                st.markdown(tx.get("category") or "—")
            with c5:
                st.markdown(f"**{merchant}**" + (f"  ·  *{bank}*" if bank else ""))

            show_tag_section(token, tx_id, tx.get("tags", []), ENDPOINTS, edit_key=f"b_editing_{tx_id}")

            if st.session_state.get(f"b_editing_{tx_id}", False):
                show_browse_edit_form(token, tx)


def show_browse_edit_form(token: str, tx: dict):
    tx_id = tx["id"]
    with st.form(key=f"b_edit_form_{tx_id}"):
        st.markdown("**Edit Transaction**")
        c1, c2 = st.columns(2)
        with c1:
            merchant = st.text_input("Merchant", value=tx.get("merchant", ""), key=f"b_merch_{tx_id}")
            amount = st.number_input("Amount", value=float(tx["amount"]), key=f"b_amt_{tx_id}")
            owner_options = ["—", "Rafael", "Heloisa", "Shared"]
            current_owner = tx.get("owner") or "—"
            owner = st.selectbox("Owner", owner_options,
                index=owner_options.index(current_owner) if current_owner in owner_options else 0,
                key=f"b_owner_{tx_id}")
        with c2:
            description = st.text_input("Description", value=tx.get("description") or "", key=f"b_desc_{tx_id}")
            cat_options = ["—"] + CATEGORIES
            current_cat = tx.get("category") or "—"
            category = st.selectbox("Category", cat_options,
                index=cat_options.index(current_cat) if current_cat in cat_options else 0,
                key=f"b_cat_{tx_id}")
        if st.form_submit_button("Save"):
            data = {"merchant": merchant, "amount": amount, "description": description}
            if owner != "—":
                data["owner"] = owner
            if category != "—":
                data["category"] = category
            success, response = make_api_call(
                "PATCH",
                f"{ENDPOINTS['update_transaction']}/{tx_id}",
                data=data,
                token=token,
            )
            if success:
                st.success("✓ Updated")
                st.session_state[f"b_editing_{tx_id}"] = False
                st.rerun()
            else:
                st.error(f"Failed: {response}")
    if st.button("Cancel", key=f"b_cancel_{tx_id}"):
        st.session_state[f"b_editing_{tx_id}"] = False
        st.rerun()


def show_monthly_chart(token: str):
    success, response = make_api_call("GET", ENDPOINTS["analytics_by_month"], token=token, params={"months": 12})
    if not success:
        st.error(f"Failed to load monthly data: {response}")
        return
    data = response.get("months", [])
    if not data:
        st.info("No data yet")
        return
    months = [d["month"] for d in data]
    totals = [d["total"] for d in data]
    fig = go.Figure(data=[go.Bar(x=months, y=totals, text=[f"€{t:,.0f}" for t in totals], textposition="outside")])
    fig.update_layout(xaxis_title="Month", yaxis_title="Total (€)", height=350, margin={"t": 20})
    st.plotly_chart(fig, use_container_width=True)


def show_owner_chart(token: str, date_from, date_to):
    success, response = make_api_call(
        "GET", ENDPOINTS["analytics_by_owner"], token=token,
        params={"date_from": date_from.isoformat(), "date_to": date_to.isoformat()},
    )
    if not success:
        st.error(f"Failed to load owner data: {response}")
        return
    data = response.get("owners", [])
    if not data:
        st.info("No categorized owner data for this period")
        return
    owners = [d["owner"] for d in data]
    totals = [d["total"] for d in data]
    colors = {"Rafael": "#4C78A8", "Heloisa": "#E45756", "Shared": "#72B7B2"}
    bar_colors = [colors.get(o, "#BAB0AC") for o in owners]
    fig = go.Figure(data=[go.Bar(
        x=owners, y=totals,
        marker_color=bar_colors,
        text=[f"€{t:,.0f}" for t in totals], textposition="outside",
    )])
    fig.update_layout(yaxis_title="Total (€)", height=300, margin={"t": 20})
    st.plotly_chart(fig, use_container_width=True)


def show_category_trends_chart(token: str):
    success, response = make_api_call("GET", ENDPOINTS["analytics_category_trends"], token=token, params={"months": 6})
    if not success:
        st.error(f"Failed to load category trends: {response}")
        return
    trends = response.get("trends", [])
    if not trends:
        st.info("No data yet")
        return
    # Pivot: category → {month: total}
    from collections import defaultdict
    cat_month: dict[str, dict[str, float]] = defaultdict(dict)
    all_months: set[str] = set()
    for row in trends:
        cat_month[row["category"]][row["month"]] = row["total"]
        all_months.add(row["month"])
    months_sorted = sorted(all_months)
    # Top 6 categories by total spend
    cat_totals = {cat: sum(mv.values()) for cat, mv in cat_month.items()}
    top_cats = sorted(cat_totals, key=cat_totals.get, reverse=True)[:6]
    fig = go.Figure()
    for cat in top_cats:
        fig.add_trace(go.Bar(
            name=cat,
            x=months_sorted,
            y=[cat_month[cat].get(m, 0) for m in months_sorted],
        ))
    fig.update_layout(
        barmode="stack", xaxis_title="Month", yaxis_title="Total (€)",
        height=380, legend={"orientation": "h", "y": -0.2}, margin={"t": 20},
    )
    st.plotly_chart(fig, use_container_width=True)


def export_csv(token: str, date_from, date_to):
    """Export transactions as CSV."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["export_transactions"],
        token=token,
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "format": "csv",
        },
    )

    if not success:
        st.error(f"Failed to export: {response}")
        return

    # Response should be CSV content
    csv_content = response

    filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.csv"

    st.download_button(
        label="📥 Download CSV",
        data=csv_content,
        file_name=filename,
        mime="text/csv",
    )
