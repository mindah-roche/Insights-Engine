import requests
import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load environment variables from backend/.env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
load_dotenv(dotenv_path=dotenv_path)

DB_URI = os.getenv("DB_URI")
API_KEY = os.getenv("API_KEY")

if not DB_URI:
    st.error("DB_URI not loaded. Check .env path or contents.")
    st.stop()

# Connect to database
engine = create_engine(DB_URI)

st.set_page_config(page_title="AI Real Estate Dashboard", layout="wide")

@st.cache_data
def load_data():
    query = """
    SELECT 
        o.id AS order_id,
        o.order_date,
        o.quantity,
        p.id AS product_id,
        p.name AS product_name,
        p.category,
        p.price,
        u.name AS user_name,
        u.email
    FROM orders o
    LEFT JOIN products p ON o.product_id = p.id
    LEFT JOIN users u ON o.user_id = u.id
    """
    df = pd.read_sql(query, engine)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["revenue"] = df["quantity"] * df["price"]
    return df

@st.cache_data
def convert_df_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8")

df = load_data()

# Sidebar filters
with st.sidebar:
    st.header("Filters")

    categories = st.multiselect("Unit Type", df["category"].dropna().unique(), default=list(df["category"].dropna().unique()))
    product_names = st.multiselect("Property", sorted(df["product_name"].dropna().unique()))

    date_mode = st.radio("Filter By Date:", ["Single Date", "Date Range"], horizontal=True)
    if date_mode == "Single Date":
        selected_date = st.date_input("Select Date", value=df["order_date"].min().date())
        start_date = end_date = selected_date
    else:
        start_date = st.date_input("Start Date", value=df["order_date"].min().date())
        end_date = st.date_input("End Date", value=df["order_date"].max().date())
        if start_date > end_date:
            st.warning("Start date cannot be after end date.")
            st.stop()

    price_min, price_max = st.slider("Price Range (KES)", min_value=0, max_value=int(df["price"].max()), value=(0, int(df["price"].max())))

# Filter application
filtered_df = df[
    (df["order_date"].dt.date >= start_date) &
    (df["order_date"].dt.date <= end_date) &
    (df["price"] >= price_min) &
    (df["price"] <= price_max)
]

if categories:
    filtered_df = filtered_df[filtered_df["category"].isin(categories)]
if product_names:
    filtered_df = filtered_df[filtered_df["product_name"].isin(product_names)]

# Tabs
overview_tab, ai_tab, raw_data_tab = st.tabs(["📊 Overview", "🤖 AI Assistant", "📄 Raw Data"])

with overview_tab:
    st.title("Portfolio Dashboard")

    # Key Metrics
    with st.expander("Key Metrics", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Units", filtered_df["order_id"].nunique())
        col2.metric("Revenue", f"KES {filtered_df['revenue'].sum():,.2f}")
        col3.metric("Tenants", filtered_df["user_name"].nunique())

        col4, col5, col6 = st.columns(3)
        col4.metric("Avg Monthly Rent", f"KES {filtered_df['price'].mean():,.0f}")
        col5.metric("Avg Lease Duration", f"{filtered_df['quantity'].mean():.1f} months")
        top_category = (
            filtered_df["category"].value_counts().idxmax()
            if not filtered_df["category"].isnull().all()
            else "N/A"
        )
        col6.metric("Top Unit Type", top_category)

        col7, _, _ = st.columns(3)
        repeat_tenants = (
            filtered_df.groupby("user_name")["order_id"]
            .count()
            .reset_index()
        )
        repeat_count = repeat_tenants[repeat_tenants["order_id"] > 1].shape[0]
        col7.metric("Repeat Tenants", repeat_count)

    # Product Performance
    with st.expander("Product Performance", expanded=True):
        product_perf = (
            filtered_df.groupby("product_name")["revenue"]
            .sum()
            .reset_index()
            .sort_values(by="revenue", ascending=False)
        )
        if not product_perf.empty:
            chart = alt.Chart(product_perf).mark_bar().encode(
                x=alt.X("product_name:N", sort="-y", title="Product Name"),
                y=alt.Y("revenue:Q", title="Revenue (KES)"),
                tooltip=["product_name", "revenue"]
            ).properties(
                title="Revenue by Product",
                width=700,
                height=400
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No product performance data available.")

    # Top Revenue-Generating Properties
    with st.expander("Top Revenue-Generating Properties", expanded=True):
        top_units = (
            filtered_df.groupby("product_name")["revenue"]
            .sum()
            .reset_index()
            .sort_values(by="revenue", ascending=False)
            .head(10)
        )
        if not top_units.empty:
            chart = alt.Chart(top_units).mark_bar().encode(
                x=alt.X("product_name:N", sort="-y", title="Product Name"),
                y=alt.Y("revenue:Q", title="Revenue (KES)"),
                tooltip=["product_name", "revenue"]
            ).properties(
                title="Top 10 Revenue-Generating Properties",
                width=700,
                height=400
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No property revenue data available.")

    # Leases Over Time
    with st.expander("Leases Over Time", expanded=True):
        trend = filtered_df.copy()
        if not trend.empty:
            trend["lease_day"] = trend["order_date"].dt.date
            trend_grouped = trend.groupby("lease_day")["order_id"].count().reset_index()
            chart = alt.Chart(trend_grouped).mark_line(point=True).encode(
                x=alt.X("lease_day:T", title="Date"),
                y=alt.Y("order_id:Q", title="Lease Count"),
                tooltip=["lease_day", "order_id"]
            ).properties(
                title="Leases Over Time",
                width=700,
                height=400
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No lease data available for selected filters.")

    # Lease Duration Distribution
    with st.expander("Lease Duration Distribution", expanded=False):
        duration_dist = filtered_df["quantity"].value_counts().reset_index()
        duration_dist.columns = ["quantity", "count"]
        chart = alt.Chart(duration_dist).mark_bar().encode(
            x=alt.X("quantity:O", title="Lease Duration (Months)"),
            y=alt.Y("count:Q", title="Number of Leases"),
            tooltip=["quantity", "count"]
        ).properties(
            width=700, height=300, title="Lease Duration Distribution"
        )
        st.altair_chart(chart, use_container_width=True)

    # Unit Type Distribution
    with st.expander("Unit Type Distribution", expanded=False):
        unit_counts = filtered_df["category"].value_counts().reset_index()
        unit_counts.columns = ["category", "count"]
        chart = alt.Chart(unit_counts).mark_bar().encode(
            x=alt.X("category:N", title="Unit Type"),
            y=alt.Y("count:Q", title="Count"),
            tooltip=["category", "count"]
        ).properties(
            width=700, height=300, title="Unit Type Distribution"
        )
        st.altair_chart(chart, use_container_width=True)

    # Download
    with st.expander("*Download Filtered Data", expanded=False):
        st.download_button("Download CSV", convert_df_to_csv(filtered_df), "leases.csv", "text/csv")

with ai_tab:
    st.header("🤖 Ask AI About Your Portfolio")
    question = st.text_input("Ask a question about your data")
    if question:
        with st.spinner("Thinking..."):
            try:
                headers = {"X-API-Key": API_KEY} if API_KEY else {}
                response = requests.post("http://localhost:8000/ask", json={"question": question}, headers=headers)
                result = response.json()
                if "result" in result:
                    ai_df = pd.DataFrame(result["result"])
                    if ai_df.empty:
                        st.info("No results found.")
                    else:
                        st.dataframe(ai_df)
                        st.download_button("Download AI Result", convert_df_to_csv(ai_df), "ai_result.csv", "text/csv")
                elif "message" in result:
                    st.warning(result["message"])
                else:
                    st.error("Unexpected response from backend.")
            except Exception as e:
                st.error(f"Error: {e}")

with raw_data_tab:
    st.header("📄 Raw Leases Data")
    st.dataframe(filtered_df)
