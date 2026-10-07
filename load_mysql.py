import pandas as pd
import os
from sqlalchemy import create_engine, String
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

url = URL.create(
    "mysql+pymysql",
    username="root",         
    password=os.environ["MYSQL_PASSWORD"], 
    host="localhost",
    port=3306,
    database="olist",
)
engine = create_engine(url)

files = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "category_translation": "product_category_name_translation.csv"
}

for table, csv in files.items():
    df = pd.read_csv(f"data/{csv}")
    text_cols = {c: String(100) for c in df.select_dtypes("object").columns}
    df.to_sql(table, engine, if_exists="replace", index=False,
              dtype=text_cols, chunksize=5000)
    print(table, df.shape)