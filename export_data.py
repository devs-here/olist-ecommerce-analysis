"""Run once locally: exports every query result to app_data/*.csv for the Streamlit app."""
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()
os.makedirs("app_data", exist_ok=True)

engine = create_engine(URL.create(
    "mysql+pymysql",
    username="root",
    password=os.environ["MYSQL_PASSWORD"],
    host="localhost",
    port=3306,
    database="olist",
))

# csv name -> query (same order as queries/olist_queries.sql)
QUERIES = {
    # 1. order count by status
    "orders_by_status": """
        SELECT order_status, COUNT(*) AS total_orders
        FROM orders
        GROUP BY order_status
        ORDER BY total_orders DESC;
    """,
    # 2. top 5 products by revenue
    "top_products": """
        SELECT product_id, ROUND(SUM(price), 2) AS total_revenue
        FROM order_items
        GROUP BY product_id
        ORDER BY total_revenue DESC
        LIMIT 5;
    """,
    # 3. top 5 categories by revenue
    "top_categories_pt": """
        SELECT p.product_category_name, ROUND(SUM(oi.price), 2) AS total_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY product_category_name
        ORDER BY total_revenue DESC
        LIMIT 5;
    """,
    # 4. same categories, with items sold
    "categories_items_sold": """
        SELECT p.product_category_name,
               COUNT(*) AS item_sold,
               ROUND(SUM(oi.price), 2) AS total_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY product_category_name
        ORDER BY total_revenue DESC
        LIMIT 5;
    """,
    # 5. monthly revenue, delivered only
    "monthly_revenue": """
        SELECT LEFT(o.order_purchase_timestamp, 7) AS order_month,
               ROUND(SUM(oi.price), 2) AS total_revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY order_month
        ORDER BY order_month;
    """,
    # 6. revenue by payment type, delivered only
    "payment_types": """
        SELECT p.payment_type,
               COUNT(*) AS payments,
               ROUND(SUM(p.payment_value), 2) AS total_paid
        FROM order_payments p
        JOIN orders o ON p.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY payment_type
        ORDER BY total_paid DESC;
    """,
    # 7. top 10 customers by spending
    "top_customers": """
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
    """,
    # 8. months with revenue above 800k
    "high_revenue_months": """
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
    """,
    # 9. month over month growth (LAG)
    "monthly_growth": """
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
    """,
    # 10. customers with more than one delivered order
    "repeat_customers": """
        SELECT c.customer_unique_id,
               COUNT(DISTINCT o.order_id) AS total_orders
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id
        HAVING COUNT(DISTINCT o.order_id) > 1
        ORDER BY total_orders DESC
        LIMIT 10;
    """,
    # 11. top 10 categories by revenue, English names
    "top_categories": """
        SELECT t.product_category_name_english AS category,
               ROUND(SUM(oi.price), 2) AS revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN category_translation t ON p.product_category_name = t.product_category_name
        GROUP BY t.product_category_name_english
        ORDER BY revenue DESC
        LIMIT 10;
    """,
}

for i, (name, sql) in enumerate(QUERIES.items(), start=1):
    df = pd.read_sql_query(sql, engine)
    df.to_csv(f"app_data/{name}.csv", index=False)
    print(f"{i:>2}. saved app_data/{name}.csv ({len(df)} rows)")
