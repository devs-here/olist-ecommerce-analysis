-- Olist e-commerce analysis (MySQL, database: olist)


-- 1. order count by status
SELECT order_status, COUNT(*) AS total_orders
FROM olist.orders
GROUP BY order_status
ORDER BY total_orders DESC;


-- 2. top 5 products by revenue
SELECT product_id, ROUND(SUM(price),2) AS total_revenue
FROM olist.order_items
GROUP BY product_id
ORDER BY total_revenue DESC
LIMIT 5;


-- 3. top 5 categories by revenue
SELECT p.product_category_name, ROUND(SUM(oi.price), 2) AS total_revenue
FROM olist.order_items oi
JOIN olist.products p ON oi.product_id = p.product_id
GROUP BY product_category_name
ORDER BY total_revenue DESC
LIMIT 5;


-- 4. same categories, with items sold next to revenue
SELECT p.product_category_name, 
        COUNT(*) AS item_sold,
        ROUND(SUM(oi.price), 2) AS total_revenue
FROM olist.order_items oi
JOIN olist.products p ON oi.product_id = p.product_id
GROUP BY product_category_name
ORDER BY total_revenue DESC
LIMIT 5;


-- 5. monthly revenue, delivered orders only
SELECT LEFT(o.order_purchase_timestamp, 7) AS order_month,
        ROUND(SUM(oi.price), 2) AS total_revenue
FROM olist.orders o
JOIN olist.order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY order_month
ORDER BY order_month;


-- 6. revenue by payment type, delivered only
SELECT p.payment_type,
       COUNT(*) AS payments,
       ROUND(SUM(p.payment_value), 2) AS total_paid
FROM olist.order_payments p
JOIN olist.orders o ON p.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY payment_type
ORDER BY total_paid DESC;


-- 7. top 10 customers by spending
-- using customer_unique_id since customer_id changes with every order
SELECT c.customer_unique_id,
       COUNT(DISTINCT o.order_id) AS total_orders,
       ROUND(SUM(p.payment_value), 2) AS total_spent
FROM olist.customers c
JOIN olist.orders o ON c.customer_id = o.customer_id
JOIN olist.order_payments p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY customer_unique_id
ORDER BY total_spent DESC
LIMIT 10;


-- 8. months with revenue above 800k
WITH monthly AS (
    SELECT LEFT(o.order_purchase_timestamp, 7) AS order_month,
           ROUND(SUM(oi.price), 2) AS revenue
    FROM olist.orders o
    JOIN olist.order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY order_month
)
SELECT order_month, revenue
FROM monthly
WHERE revenue > 800000
ORDER BY order_month;


-- 9. month over month growth (LAG)
-- first month is NULL since there is nothing before it
WITH monthly AS (
    SELECT LEFT(o.order_purchase_timestamp, 7) AS order_month,
           ROUND(SUM(oi.price), 2) AS revenue
    FROM olist.orders o
    JOIN olist.order_items oi ON o.order_id = oi.order_id
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


-- 10. customers with more than one delivered order
SELECT c.customer_unique_id,
       COUNT(DISTINCT o.order_id) AS total_orders
FROM olist.customers c
JOIN olist.orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id
HAVING COUNT(DISTINCT o.order_id) > 1
ORDER BY total_orders DESC
LIMIT 10;

-- 11. top 10 categories by revenue, English names
SELECT t.product_category_name_english AS category,
       ROUND(SUM(oi.price), 2) AS revenue
FROM olist.order_items oi
JOIN olist.products p ON oi.product_id = p.product_id
JOIN olist.category_translation t ON p.product_category_name = t.product_category_name
GROUP BY t.product_category_name_english
ORDER BY revenue DESC
LIMIT 10;