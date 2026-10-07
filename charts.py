import os
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

os.makedirs("charts", exist_ok=True)
SHOW = False   # False = only save the charts, don't open windows

url = URL.create(
    "mysql+pymysql",
    username="root",
    password=os.environ["MYSQL_PASSWORD"],
    host="localhost",
    port=3306,
    database="olist",
)
engine = create_engine(url)

millions = mtick.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M")


def run(query):
    return pd.read_sql_query(query, engine)


def finish(filename):
    plt.tight_layout()
    plt.savefig(f"charts/{filename}", dpi=150, bbox_inches="tight")
    if SHOW:
        plt.show()
    plt.close()


# 1. order count by status  -> bar chart (log scale)
df1 = run("""
SELECT order_status, COUNT(*) AS total_orders
FROM orders
GROUP BY order_status
ORDER BY total_orders DESC;
""")
print(df1)

plt.figure(figsize=(8, 5))
sns.barplot(data=df1, x="total_orders", y="order_status", color="steelblue")
plt.xscale("log")
plt.title("Orders by status (log scale)")
plt.xlabel("Orders")
plt.ylabel("")
finish("01_orders_by_status.png")


# 2. top 5 products by revenue  -> bar chart
df2 = run("""
SELECT product_id, ROUND(SUM(price), 2) AS total_revenue
FROM order_items
GROUP BY product_id
ORDER BY total_revenue DESC
LIMIT 5;
""")
print(df2)

df2["label"] = df2["product_id"].str[:8]
plt.figure(figsize=(8, 4))
sns.barplot(data=df2, x="total_revenue", y="label", color="steelblue")
plt.title("Top 5 products by revenue")
plt.xlabel("Revenue (BRL)")
plt.ylabel("Product ID (first 8 characters)")
finish("02_top_products.png")


# 3. top 5 categories by revenue (Portuguese names)  -> table only
df3 = run("""
SELECT p.product_category_name, ROUND(SUM(oi.price), 2) AS total_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY product_category_name
ORDER BY total_revenue DESC
LIMIT 5;
""")
print(df3)


# 4. same categories with items sold  -> bar chart with item counts
df4 = run("""
SELECT p.product_category_name,
       COUNT(*) AS item_sold,
       ROUND(SUM(oi.price), 2) AS total_revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY product_category_name
ORDER BY total_revenue DESC
LIMIT 5;
""")
print(df4)

plt.figure(figsize=(9, 4))
sns.barplot(data=df4, x="total_revenue", y="product_category_name", color="steelblue")
for i, row in df4.iterrows():
    plt.text(row["total_revenue"], i, f"  {row['item_sold']:,} items", va="center")
plt.xlim(0, df4["total_revenue"].max() * 1.25)
plt.gca().xaxis.set_major_formatter(millions)
plt.title("Top 5 categories: revenue and items sold")
plt.xlabel("Revenue (BRL, millions)")
plt.ylabel("")
finish("04_categories_items_sold.png")


# 5. monthly revenue, delivered only  -> line chart (interactive HTML)
df5 = run("""
SELECT LEFT(o.order_purchase_timestamp, 7) AS order_month,
       ROUND(SUM(oi.price), 2) AS total_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY order_month
ORDER BY order_month;
""")
print(df5)

df5["order_month"] = pd.to_datetime(df5["order_month"])
df5_plot = df5[df5["order_month"] >= "2017-01-01"]

fig = px.line(
    df5_plot, x="order_month", y="total_revenue", markers=True,
    title="Monthly revenue (delivered orders)",
)
fig.add_annotation(x="2017-11-01", y=987765.37, text="Black Friday", showarrow=True)
fig.update_layout(xaxis_title="Month", yaxis_title="Revenue (BRL)", template="plotly_white")
fig.write_html("charts/05_monthly_revenue.html")
if SHOW:
    fig.show()


# 6. revenue by payment type, delivered only  -> bar chart
df6 = run("""
SELECT p.payment_type,
       COUNT(*) AS payments,
       ROUND(SUM(p.payment_value), 2) AS total_paid
FROM order_payments p
JOIN orders o ON p.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY payment_type
ORDER BY total_paid DESC;
""")
print(df6)

fig = px.bar(
    df6, x="payment_type", y="total_paid",
    title="Total paid by payment type, incl. shipping (delivered orders)"
)
fig.update_layout(xaxis_title="Payment type", yaxis_title="Total paid (BRL)", template="plotly_white")
fig.write_html("charts/06_payment_types.html")
if SHOW:
    fig.show()


# 7. top 10 customers by spending  -> bar chart
df7 = run("""
SELECT c.customer_unique_id,
       COUNT(DISTINCT o.order_id) AS total_orders,
       ROUND(SUM(p.payment_value), 2) AS total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY customer_unique_id
ORDER BY total_spent DESC
LIMIT 10;
""")
print(df7)

df7["label"] = df7["customer_unique_id"].str[:8]
plt.figure(figsize=(9, 5))
sns.barplot(data=df7, x="total_spent", y="label", color="steelblue")
plt.title("Top 10 customers by total spent (delivered orders)")
plt.xlabel("Total spent (BRL)")
plt.ylabel("Customer ID (first 8 characters)")
finish("07_top_customers.png")


# 8. months with revenue above 800k  -> table only
df8 = run("""
WITH monthly AS (
    SELECT LEFT(o.order_purchase_timestamp, 7) AS order_month,
           ROUND(SUM(oi.price), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY order_month
)
SELECT order_month, revenue
FROM monthly
WHERE revenue > 800000
ORDER BY order_month;
""")
print(df8)


# 9. month over month growth (LAG)  -> green/red bar chart
df9 = run("""
WITH monthly AS (
    SELECT LEFT(o.order_purchase_timestamp, 7) AS order_month,
           ROUND(SUM(oi.price), 2) AS revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY order_month
)
SELECT order_month,
       revenue,
       LAG(revenue) OVER (ORDER BY order_month) AS prev_revenue,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY order_month))
             / LAG(revenue) OVER (ORDER BY order_month) * 100, 1) AS growth_pct
FROM monthly
ORDER BY order_month;
""")
print(df9)

df9_plot = df9[df9["order_month"] >= "2017-02"]
colors = ["green" if g >= 0 else "red" for g in df9_plot["growth_pct"]]

plt.figure(figsize=(11, 5))
plt.bar(df9_plot["order_month"], df9_plot["growth_pct"], color=colors)
plt.axhline(0, color="black", linewidth=0.8)
plt.xticks(rotation=45)
plt.title("Month-over-month revenue growth (delivered orders)")
plt.xlabel("Month")
plt.ylabel("Growth (%)")
finish("09_monthly_growth.png")


# 10. customers with more than one delivered order  -> bar chart
df10 = run("""
SELECT c.customer_unique_id,
       COUNT(DISTINCT o.order_id) AS total_orders
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id
HAVING COUNT(DISTINCT o.order_id) > 1
ORDER BY total_orders DESC
LIMIT 10;
""")
print(df10)

df10["label"] = df10["customer_unique_id"].str[:8]
plt.figure(figsize=(8, 5))
sns.barplot(data=df10, x="total_orders", y="label", color="steelblue")
plt.title("Top 10 repeat customers by number of orders")
plt.xlabel("Delivered orders")
plt.ylabel("Customer ID (first 8 characters)")
finish("10_repeat_customers.png")


# 11. top 10 categories by revenue, English names  -> bar chart
df11 = run("""
SELECT t.product_category_name_english AS category,
       ROUND(SUM(oi.price), 2) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN category_translation t ON p.product_category_name = t.product_category_name
GROUP BY t.product_category_name_english
ORDER BY revenue DESC
LIMIT 10;
""")
print(df11)

fig = px.bar(
    df11, x="revenue", y="category", orientation="h",
    title="Top 10 product categories by revenue",
)
fig.update_yaxes(autorange="reversed")
fig.update_layout(xaxis_title="Revenue (BRL)", yaxis_title="", template="plotly_white")
fig.write_html("charts/11_top_categories.html")
if SHOW:
    fig.show()