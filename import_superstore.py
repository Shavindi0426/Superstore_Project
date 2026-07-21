"""
import_superstore.py
Loads superstore_clean.csv into the staging_superstore table
in the superstore_db MySQL database.

Requires: pip install pandas mysql-connector-python
"""

import pandas as pd
import mysql.connector
import math
import os
from dotenv import load_dotenv

load_dotenv()

# DATABASE CONNECTION 
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "Shaw0426@",  
    "database": "superstore_db"
}

#  FILE PATH 
CSV_PATH = "superstore_clean.csv"  

#  COLUMN MAPPING: CSV header -> staging table column
COLUMN_MAP = {
    "Row.ID": "row_id",
    "Order.ID": "order_id",
    "Order.Date": "order_date",
    "Ship.Date": "ship_date",
    "Ship.Mode": "ship_mode",
    "Customer.ID": "customer_id",
    "Customer.Name": "customer_name",
    "Segment": "segment",
    "City": "city",
    "State": "state",
    "Country": "country",
    "Region": "region",
    "Market": "market",
    "Market2": "market2",
    "Product.ID": "product_id",
    "Category": "category",
    "Sub.Category": "sub_category",
    "Product.Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
    "Shipping.Cost": "shipping_cost",
    "Order.Priority": "order_priority",
    "Year": "year",
    "weeknum": "weeknum",
}

TABLE_COLUMNS = list(COLUMN_MAP.values())


def load_csv():
    print(f"Reading {CSV_PATH} ...")
    df = pd.read_csv(
        CSV_PATH,
        encoding="utf-8",
        engine="python",       # more tolerant parser
        on_bad_lines="warn",   # print a warning for malformed rows instead of crashing
    )
    print(f"Loaded {len(df)} rows (before dropping unused columns).")

    # Keep only the columns we care about, rename to match staging table
    df = df[list(COLUMN_MAP.keys())].rename(columns=COLUMN_MAP)

    # Replace pandas NaN with None so MySQL gets proper NULLs
    df = df.where(pd.notnull(df), None)

    return df


def insert_data(df):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("Clearing existing staging data...")
    cursor.execute("TRUNCATE TABLE staging_superstore")
    conn.commit()

    placeholders = ", ".join(["%s"] * len(TABLE_COLUMNS))
    columns_sql = ", ".join(TABLE_COLUMNS)
    insert_sql = f"INSERT INTO staging_superstore ({columns_sql}) VALUES ({placeholders})"

    records = [tuple(row) for row in df[TABLE_COLUMNS].itertuples(index=False, name=None)]

    batch_size = 1000
    total = len(records)
    print(f"Inserting {total} rows in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        cursor.executemany(insert_sql, batch)
        conn.commit()
        print(f"  {min(i + batch_size, total)}/{total} rows inserted...")

    cursor.close()
    conn.close()
    print("\nDone! All data inserted into staging_superstore.")


if __name__ == "__main__":
    df = load_csv()
    insert_data(df)