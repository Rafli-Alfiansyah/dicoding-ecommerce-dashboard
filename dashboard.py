"""
Interactive E-Commerce Performance Dashboard
=============================================
Run with:  streamlit run dashboard/dashboard.py

Reads the cleaned, consolidated dataset produced by the analysis notebook
(dashboard/main_data.csv) and renders:
  - A sidebar date-range filter (on order_purchase_timestamp)
  - 3 KPI summary cards: Total Revenue, Total Orders, Total Unique Customers
  - Interactive Top 10 Product Categories by Revenue chart
  - Interactive RFM Customer Segment distribution chart
"""

import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="E-Commerce Performance Dashboard",
    page_icon="🛒",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "main_data.csv"


# ------------------------------------------------------------------
# Data loading (cached so filtering/interaction stays fast)
# ------------------------------------------------------------------
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        parse_dates=[
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    return df


@st.cache_data
def compute_rfm(df: pd.DataFrame, window_months: int = 12) -> pd.DataFrame:
    """Recomputes RFM + segments on whatever subset of orders is passed in,
    using the same logic as the analysis notebook."""
    max_date = df["order_purchase_timestamp"].max()
    window_start = max_date - pd.DateOffset(months=window_months)
    window_df = df[df["order_purchase_timestamp"] >= window_start]

    rfm = (
        window_df.groupby("customer_unique_id")
        .agg(
            last_purchase_date=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("price", "sum"),
        )
        .reset_index()
    )
    rfm["recency"] = (max_date - rfm["last_purchase_date"]).dt.days

    def score_quantile(series, ascending):
        ranks = series.rank(method="first", ascending=ascending)
        try:
            return pd.qcut(ranks, 4, labels=[1, 2, 3, 4]).astype(int)
        except ValueError:
            return pd.cut(ranks, 4, labels=[1, 2, 3, 4]).astype(int)

    rfm["R_score"] = score_quantile(rfm["recency"], ascending=True)
    rfm["F_score"] = score_quantile(rfm["frequency"], ascending=False)
    rfm["M_score"] = score_quantile(rfm["monetary"], ascending=False)

    def segment_customer(row):
        r, f, m = row["R_score"], row["F_score"], row["M_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Best Customers"
        elif r >= 3 and f >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "New / Promising"
        elif r <= 2 and f >= 3:
            return "At Risk"
        elif r <= 2 and f <= 2 and m <= 2:
            return "Hibernating"
        else:
            return "Need Attention"

    rfm["segment"] = rfm.apply(segment_customer, axis=1)
    return rfm


if not DATA_PATH.exists():
    st.error(
        f"Could not find `{DATA_PATH.name}` next to this script. "
        "Run the analysis notebook first — it saves the cleaned dataset to "
        "`dashboard/main_data.csv`."
    )
    st.stop()

main_df = load_data(DATA_PATH)

# ------------------------------------------------------------------
# Sidebar — date range filter
# ------------------------------------------------------------------
st.sidebar.header("🔎 Filters")

min_date = main_df["order_purchase_timestamp"].min().date()
max_date = main_df["order_purchase_timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Order purchase date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# date_input returns a single date until the user picks both ends — guard for that
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

mask = (
    main_df["order_purchase_timestamp"].dt.date >= start_date
) & (
    main_df["order_purchase_timestamp"].dt.date <= end_date
)
filtered_df = main_df[mask]

st.sidebar.caption(f"Showing **{len(filtered_df):,}** order-item rows out of {len(main_df):,} total.")

# ------------------------------------------------------------------
# Header + KPI cards
# ------------------------------------------------------------------
st.title("🛒 E-Commerce Performance Dashboard")
st.caption("Built on the Olist Brazilian E-Commerce Public Dataset")

if filtered_df.empty:
    st.warning("No orders fall within the selected date range. Try widening it.")
    st.stop()

total_revenue = filtered_df["price"].sum()
total_orders = filtered_df["order_id"].nunique()
total_customers = filtered_df["customer_unique_id"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"R$ {total_revenue:,.2f}")
col2.metric("Total Orders", f"{total_orders:,}")
col3.metric("Total Unique Customers", f"{total_customers:,}")

st.divider()

# ------------------------------------------------------------------
# Chart 1 — Top 10 product categories by revenue
# ------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Top 10 Product Categories by Revenue")
    category_revenue = (
        filtered_df.groupby("product_category_name_english")["price"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index(name="total_revenue")
        .sort_values("total_revenue", ascending=True)
    )
    fig1 = px.bar(
        category_revenue,
        x="total_revenue",
        y="product_category_name_english",
        orientation="h",
        labels={"total_revenue": "Total Revenue (R$)", "product_category_name_english": ""},
        text="total_revenue",
        color_discrete_sequence=["#2E86AB"],
    )
    fig1.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
    fig1.update_layout(
        height=450,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Total Revenue (R$)",
        yaxis_title=None,
    )
    st.plotly_chart(fig1, width="stretch")

# ------------------------------------------------------------------
# Chart 2 — RFM customer segment distribution
# ------------------------------------------------------------------
with right:
    st.subheader("Customer Distribution Across RFM Segments")
    rfm_df = compute_rfm(filtered_df)
    segment_counts = (
        rfm_df["segment"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "segment", "count": "customers"})
        .sort_values("customers", ascending=True)
    )
    fig2 = px.bar(
        segment_counts,
        x="customers",
        y="segment",
        orientation="h",
        labels={"customers": "Number of Customers", "segment": ""},
        text="customers",
        color="segment",
        color_discrete_sequence=px.colors.sequential.Viridis,
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        height=450,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        xaxis_title="Number of Customers",
        yaxis_title=None,
    )
    st.plotly_chart(fig2, width="stretch")

st.divider()
with st.expander("ℹ️ About RFM Segmentation"):
    st.markdown(
        """
        RFM scores each customer (`customer_unique_id`) on three dimensions using
        the last 12 months of purchase history in the current filter window:

        - **Recency** — days since their last order (lower is better)
        - **Frequency** — number of distinct orders placed
        - **Monetary** — total amount spent

        Each dimension is split into quartiles (1–4, 4 = best) and combined into
        business segments: **Best Customers**, **Loyal Customers**,
        **New / Promising**, **At Risk**, **Need Attention**, and **Hibernating**.
        """
    )
