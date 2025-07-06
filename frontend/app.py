import requests
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load .env from backend directory
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(os.getcwd()), "backend", ".env"))
load_dotenv(dotenv_path=dotenv_path)

DB_URI = os.getenv("DB_URI")
API_KEY = os.getenv("API_KEY")  # Load the API key

if not DB_URI:
    st.error("DB_URI not loaded. Check .env path or contents.")
    st.stop()

# Connect to database
engine = create_engine(DB_URI)

# Streamlit setup
st.set_page_config(page_title="AI Dashboard Assistant", layout="wide")

# Load data from database
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
        "Select Product Category", 
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
tab1, tab2, tab3 = st.tabs(["Overview", "🤖 AI Assistant", "📄 Raw Data"])

# Overview Tab
with tab1:
    st.title("Orders Dashboard")

    st.caption("**Active Filters:**")
    if date_mode == "Single Date":
        st.write(f"📅 Date: {start_date.strftime('%B %d, %Y')}")
    else:
        st.write(f"📆 Date Range: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    st.write(f"📂 Categories: {', '.join(categories) if categories else 'None'}")

    if filtered_df.empty:
        st.warning("No data matches your selected filters.")
    else:
        with st.expander("Key Metrics", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Orders", filtered_df["order_id"].nunique())
            col2.metric("Total Revenue", f"${filtered_df['revenue'].sum():,.2f}")
            col3.metric("Unique Users", filtered_df["user_name"].nunique())

        with st.expander("📆 Orders Over Time", expanded=True):
            orders_by_day = filtered_df.copy()
            orders_by_day["order_day"] = orders_by_day["order_date"].dt.date
            orders_grouped = orders_by_day.groupby("order_day")["order_id"].count()
            st.line_chart(orders_grouped)

        with st.expander("⬇️ Download Data", expanded=False):
            csv = convert_df_to_csv(filtered_df)
            st.download_button(
                label="Download Filtered Orders as CSV",
                data=csv,
                file_name='filtered_orders.csv',
                mime='text/csv',
            )

# AI Assistant Tab
with tab2:
    st.header("Ask AI About Your Data")
    st.caption("Example: 'Which category had the highest revenue?'")

    question = st.text_input("Type your question")
    if question:
        with st.spinner("Thinking..."):
            try:
                headers = {"X-API-Key": API_KEY}
                response = requests.post(
                    "http://localhost:8000/ask",
                    json={"question": question},
                    headers=headers  # ← Secure the API request
                )
                result = response.json()

                if "result" in result:
                    st.success("AI Result:")
                    ai_df = pd.DataFrame(result["result"])

                    if ai_df.empty:
                        st.info("The query returned no results.")
                    else:
                        # Clean column names
                        ai_df.columns = [col.replace("_", " ").title() for col in ai_df.columns]

                        # Format numeric values
                        for col in ai_df.select_dtypes(include=["float", "int"]):
                            if "revenue" in col.lower() or "amount" in col.lower() or "total" in col.lower():
                                ai_df[col] = ai_df[col].map(lambda x: f"${x:,.2f}")
                            else:
                                ai_df[col] = ai_df[col].map(lambda x: round(x, 2))

                        st.dataframe(ai_df)

                        # Optional: Summary for one row
                        if len(ai_df) == 1:
                            row = ai_df.iloc[0]
                            summary_parts = [f"**{col}**: {val}" for col, val in row.items()]
                            st.markdown("Summary: " + " | ".join(summary_parts))

                        # Chart rendering
                        with st.expander("AI-Generated Chart", expanded=True):
                            chart_rendered = False

                            if "Category" in ai_df.columns and any("Revenue" in col for col in ai_df.columns):
                                revenue_col = next(col for col in ai_df.columns if "Revenue" in col)
                                st.bar_chart(ai_df.set_index("Category")[revenue_col])
                                chart_rendered = True

                            elif "Order Date" in ai_df.columns and len(ai_df.select_dtypes(include="number").columns) >= 1:
                                ai_df["Order Date"] = pd.to_datetime(ai_df["Order Date"])
                                numeric_col = ai_df.select_dtypes(include="number").columns[0]
                                st.line_chart(ai_df.set_index("Order Date")[numeric_col])
                                chart_rendered = True

                            elif "Name" in ai_df.columns and any("Total" in col for col in ai_df.columns):
                                total_col = next(col for col in ai_df.columns if "Total" in col)
                                st.bar_chart(ai_df.set_index("Name")[total_col])
                                chart_rendered = True

                            elif len(ai_df.columns) == 2 and ai_df.dtypes[1] in ["int64", "float64"]:
                                st.bar_chart(ai_df.set_index(ai_df.columns[0])[ai_df.columns[1]])
                                chart_rendered = True

                            if not chart_rendered:
                                st.info("No chart pattern matched this result.")

                        with st.expander("⬇️ Download AI Result"):
                            csv = convert_df_to_csv(ai_df)
                            st.download_button("Download as CSV", data=csv, file_name="ai_result.csv", mime="text/csv")

                elif "message" in result:
                    st.warning(result["message"])
                else:
                    st.error("Unexpected response from the AI assistant.")
            except Exception as e:
                st.error(f"Failed to contact AI API: {e}")

# Raw Data Tab
with tab3:
    st.header("Filtered Orders Table")
    st.caption(f"{len(filtered_df)} orders match your selected filters.")
    st.dataframe(filtered_df)
