import requests
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load .env from backend directory
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
load_dotenv(dotenv_path=dotenv_path)

DB_URI = os.getenv("DB_URI")
API_KEY = os.getenv("API_KEY")  # Optional for now

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

df = load_data()

# Sidebar filters
with st.sidebar:
    st.header("Filters")

    categories = st.multiselect(
        "Unit Type", 
        options=df["category"].dropna().unique(), 
        default=df["category"].dropna().unique()
    )

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

# Apply filters
filtered_df = df[
    (df["order_date"].dt.date >= start_date) &
    (df["order_date"].dt.date <= end_date)
]
if categories:
    filtered_df = filtered_df[filtered_df["category"].isin(categories)]

@st.cache_data
def convert_df_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🤖 AI Assistant", "📄 Raw Data"])

with tab1:
    st.title("Portfolio Dashboard")

    with st.expander("Key Metrics", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Units", filtered_df["order_id"].nunique())
        col2.metric("Revenue", f"KES {filtered_df['revenue'].sum():,.2f}")
        col3.metric("Tenants", filtered_df["user_name"].nunique())

    with st.expander("Leases Over Time", expanded=True):
        trend = filtered_df.copy()
        trend["lease_day"] = trend["order_date"].dt.date
        trend_grouped = trend.groupby("lease_day")["order_id"].count()
        st.line_chart(trend_grouped)

    with st.expander("⬇️ Download", expanded=False):
        csv = convert_df_to_csv(filtered_df)
        st.download_button("Download Filtered Data", csv, "leases.csv", "text/csv")

with tab2:
    st.header("🤖 Ask AI About Your Portfolio")
    question = st.text_input("Ask a question about your data")

    if question:
        with st.spinner("Thinking..."):
            try:
                headers = {"X-API-Key": API_KEY} if API_KEY else {}
                response = requests.post(
                    "http://localhost:8000/ask",
                    json={"question": question},
                    headers=headers
                )
                result = response.json()

                if "result" in result:
                    ai_df = pd.DataFrame(result["result"])
                    if ai_df.empty:
                        st.info("No results found.")
                    else:
                        st.dataframe(ai_df)
                        csv = convert_df_to_csv(ai_df)
                        st.download_button("Download AI Result", data=csv, file_name="ai_result.csv", mime="text/csv")
                elif "message" in result:
                    st.warning(result["message"])
                else:
                    st.error("Unexpected response from AI API.")
            except Exception as e:
                st.error(f"Error contacting backend: {e}")

with tab3:
    st.header("📄 Raw Leases Data")
    st.dataframe(filtered_df)
