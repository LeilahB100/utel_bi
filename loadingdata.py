"""
UTel BI Platform – Part D: Data Loading Script
===============================================
Loads the cleaned CSV files produced by transform.py into the
MySQL utel_bi database.

Prerequisites
-------------
1. MySQL server running and accessible.
2. Database and tables already created via utel_schema.sql.
3. Install driver:  pip install mysql-connector-python
4. Edit the DB_CONFIG block below with your credentials.

Usage
-----
    python load_data.py

The script loads tables in dependency order (subscriber first, then
all fact tables) and prints a row count summary on completion.
"""

import csv
import os
import sys

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    sys.exit("mysql-connector-python not installed.\n"
             "Run:  pip install mysql-connector-python")

# ── Database connection settings ──────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "utel_bi",
    "user":     "root",          # change to your MySQL user
    "password": "root"  # change to your MySQL password
}

# ── Clean file locations (produced by transform.py) ───────────────────────
# Points to the 'clean' subfolder that transform.py creates
CLEAN_DIR = r"C:\Users\personal\Desktop\assignment\clean"

FILES = {
    "subscriber":           os.path.join(CLEAN_DIR, "subscribers_clean.csv"),
    "_call":                 os.path.join(CLEAN_DIR, "calls_clean.csv"),
    "sms":                  os.path.join(CLEAN_DIR, "sms_clean.csv"),
    "airtime_sale":         os.path.join(CLEAN_DIR, "airtime_sales_clean.csv"),
    "internet_bundle_sale": os.path.join(CLEAN_DIR, "internet_bundle_sales_clean.csv"),
    "fibre_subscription":   os.path.join(CLEAN_DIR, "fibre_subscriptions_clean.csv"),
}

# ── Column mappings: CSV column → table column ────────────────────────────
COLUMN_MAP = {
    "subscriber": {
        "SubscriberID":    "subscriber_id",
        "MSISDN":          "msisdn",
        "SubscriberName":  "subscriber_name",
        "Gender":          "gender",
        "Region":          "region",
        "ActivationDate":  "activation_date",
        "Status":          "status",
    },
    "_call": {
        "CallID":           "call_id",
        "CallingMSISDN":    "calling_msisdn",
        "CalledMSISDN":     "called_msisdn",
        "CallDate":         "call_date",
        "DurationSeconds":  "duration_seconds",
        "ChargeAmount":     "charge_amount",
        "CallType":         "call_type",
    },
    "sms": {
        "SMSID":               "sms_id",
        "SourceMSISDN":        "source_msisdn",
        "DestinationMSISDN":   "destination_msisdn",
        "SMSDate":             "sms_date",
        "Direction":           "direction",
        "MessageType":         "message_type",
        "ChargeAmount":        "charge_amount",
    },
    "airtime_sale": {
        "SaleID":       "sale_id",
        "MSISDN":       "msisdn",
        "PurchaseDate": "purchase_date",
        "Amount":       "amount",
        "Channel":      "channel",
    },
    "internet_bundle_sale": {
        "BundleSaleID": "bundle_sale_id",
        "MSISDN":       "msisdn",
        "BundleName":   "bundle_name",
        "PurchaseDate": "purchase_date",
        "Amount":       "amount",
        "ValidityDays": "validity_days",
    },
    "fibre_subscription": {
        "SubscriptionID":   "subscription_id",
        "MSISDN":           "msisdn",
        "PackageName":      "package_name",
        "SubscriptionDate": "subscription_date",
        "MonthlyFee":       "monthly_fee",
        "Status":           "status",
    },
}

# ── Core loader ───────────────────────────────────────────────────────────

def load_table(cursor, table: str, csv_path: str) -> int:
    """Load all rows from csv_path into table. Returns number of rows inserted."""
    col_map = COLUMN_MAP[table]

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    if not rows:
        print(f"  [WARN] {csv_path} is empty – nothing loaded into {table}")
        return 0

    db_cols = list(col_map.values())
    placeholders = ", ".join(["%s"] * len(db_cols))
    sql = (
        f"INSERT INTO {table} ({', '.join(db_cols)}) "
        f"VALUES ({placeholders})"
    )

    def row_values(row):
        values = []
        for csv_col, _ in col_map.items():
            v = row.get(csv_col, "").strip()
            values.append(None if v == "" else v)
        return values

    data = [row_values(r) for r in rows]
    cursor.executemany(sql, data)
    return len(data)


def main():
    print("\n" + "═" * 60)
    print("  UTel BI Platform – Data Loader")
    print("═" * 60)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        sys.exit(f"Connection failed: {e}")

    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    totals = {}
    order = [
        "subscriber",
        "_call",
        "sms",
        "airtime_sale",
        "internet_bundle_sale",
        "fibre_subscription",
    ]

    for table in order:
        csv_path = FILES[table]
        if not os.path.isfile(csv_path):
            print(f"  [SKIP] {csv_path} not found")
            continue
        try:
            n = load_table(cursor, table, csv_path)
            conn.commit()
            totals[table] = n
            print(f"  ✓  {table:<28}  {n:>4} rows loaded")
        except Error as e:
            conn.rollback()
            print(f"  ✗  {table:<28}  ERROR: {e}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    cursor.close()
    conn.close()

    print("\n" + "─" * 60)
    print(f"  Total rows loaded: {sum(totals.values())}")
    print("─" * 60 + "\n")
 

if __name__ == "__main__":
    main()
