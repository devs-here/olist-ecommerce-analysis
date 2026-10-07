import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Olist E-Commerce Analysis", page_icon="📦", layout="wide")


@st.cache_data
def load(name):
    return pd.read_csv(f"app_data/{name}.csv")


st.title("📦 Olist E-Commerce Sales Analysis")
st.caption("SQL (MySQL) + Python analysis of the Olist Brazilian e-commerce dataset")

monthly = load("monthly_revenue")
status = load("orders_by_status")
payments = load("payment_types")

# Headline metrics
c1, c2, c3 = st.columns(3)
c1.metric("Delivered revenue (items)", f"R$ {monthly['total_revenue'].sum() / 1e6:.1f}M")
c2.metric("Total orders", f"{status['total_orders'].sum():,}")
c3.metric("Best month", monthly.loc[monthly["total_revenue"].idxmax(), "order_month"])

tab1, tab2, tab3, tab4 = st.tabs(["Revenue", "Products & categories", "Customers", "Orders & payments"])

with tab1:
    m = monthly[monthly["order_month"] >= "2017-01"]
    fig = px.line(m, x="order_month", y="total_revenue", markers=True,
                  title="Monthly revenue (delivered orders)")
    fig.add_annotation(x="2017-11", y=987765.37, text="Black Friday", showarrow=True)
    fig.update_layout(xaxis_title="Month", yaxis_title="Revenue (BRL)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    g = load("monthly_growth")
    g = g[g["order_month"] >= "2017-02"].copy()
    g["direction"] = g["growth_pct"].apply(lambda x: "Growth" if x >= 0 else "Decline")
    fig = px.bar(g, x="order_month", y="growth_pct", color="direction",
                 color_discrete_map={"Growth": "green", "Decline": "red"},
                 title="Month-over-month revenue growth (%)")
    fig.update_layout(xaxis_title="Month", yaxis_title="Growth (%)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with tab1:
    st.subheader("Months with revenue above R$ 800k")
    st.dataframe(load("high_revenue_months"), hide_index=True, use_container_width=True)

with tab2:
    st.subheader("Top 5 categories by revenue (Portuguese names)")
    st.dataframe(load("top_categories_pt"), hide_index=True, use_container_width=True)
    cats = load("top_categories")
    fig = px.bar(cats, x="revenue", y="category", orientation="h",
                 title="Top 10 product categories by revenue")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(xaxis_title="Revenue (BRL)", yaxis_title="", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        prods = load("top_products").copy()
        prods["label"] = prods["product_id"].str[:8]
        fig = px.bar(prods, x="total_revenue", y="label", orientation="h",
                     title="Top 5 products by revenue")
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="Revenue (BRL)", yaxis_title="Product ID", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        ci = load("categories_items_sold")
        fig = px.bar(ci, x="total_revenue", y="product_category_name", orientation="h",
                     hover_data=["item_sold"], title="Top 5 categories (Portuguese names)")
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="Revenue (BRL)", yaxis_title="", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    left, right = st.columns(2)
    with left:
        top = load("top_customers").copy()
        top["label"] = top["customer_unique_id"].str[:8]
        fig = px.bar(top, x="total_spent", y="label", orientation="h",
                     title="Top 10 customers by total spent")
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="Total spent (BRL)", yaxis_title="Customer ID", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        rep = load("repeat_customers").copy()
        rep["label"] = rep["customer_unique_id"].str[:8]
        fig = px.bar(rep, x="total_orders", y="label", orientation="h",
                     title="Top 10 repeat customers by orders")
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="Delivered orders", yaxis_title="Customer ID", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    left, right = st.columns(2)
    with left:
        fig = px.bar(status, x="total_orders", y="order_status", orientation="h", log_x=True,
                     title="Orders by status (log scale)")
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="Orders", yaxis_title="", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(payments, x="payment_type", y="total_paid",
                     title="Total paid by payment type (delivered orders)")
        fig.update_layout(xaxis_title="Payment type", yaxis_title="Total paid (BRL)", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.markdown("Source code: [github.com/devs-here/olist-ecommerce-analysis](https://github.com/devs-here/olist-ecommerce-analysis)")
