"""
UTel BI Platform – Part B: Data Transformation & Quality Checks
================================================================
Reads raw CSV files, performs all quality checks and fixes, and
writes clean CSVs ready for database loading.

Issues found and addressed
--------------------------
Subscribers
  • 1 null MSISDN (SubscriberID 11)  → dropped
  • 1 short MSISDN (71123456, 8 digits, SubscriberID 3) → invalid, dropped
  • MSISDN read as float (trailing .0)  → cast to string

Calls
  • 1 duplicate row (CallID 1)         → keep first, drop second
  • 1 null CallingMSISDN (row 1001)    → dropped
  • 1 negative DurationSeconds (CallID 4) → invalid, dropped
  • CallingMSISDN read as float        → cast to string

SMS
  • 1 null SMSDate                     → dropped

AirtimeSales
  • 1 null Amount                      → dropped
  • 1 negative Amount (SaleID 3)       → invalid, dropped
  • Date format DD/MM/YYYY             → standardised to YYYY-MM-DD

InternetBundleSales
  • 1 null BundleName                  → filled with 'Unknown'

FibreSubscriptions
  • 1 null PackageName                 → filled with 'Unknown'
  • 1 negative MonthlyFee (SubID 6)   → invalid, dropped
  • Date format DD/MM/YYYY             → standardised to YYYY-MM-DD
"""

import pandas as pd
import re
import os

# ── paths ──────────────────────────────────────────────────────────────────
# Base folder where all your CSV files live
BASE_DIR = r"C:\Users\personal\Desktop\assignment"
# the r is used to ensure that the backslshes are treated as literal characters and not escape characters.

RAW = {
    "subscribers":           os.path.join(BASE_DIR, "Subscribers.csv"),
    "calls":                 os.path.join(BASE_DIR, "Calls.csv"),
    "sms":                   os.path.join(BASE_DIR, "SMS.csv"),
    "airtime_sales":         os.path.join(BASE_DIR, "AirtimeSales.csv"),
    "internet_bundle_sales": os.path.join(BASE_DIR, "InternetBundleSales.csv"),
    "fibre_subscriptions":   os.path.join(BASE_DIR, "FibreSubscriptions.csv"),
}
#os.path.join() - combines the folder path with the file name. 


# Cleaned files will be written to a 'clean' subfolder inside the assignment folder
OUT_DIR = os.path.join(BASE_DIR, "clean")
os.makedirs(OUT_DIR, exist_ok=True)

# ── helpers ─────────────────────────────────────────────────────────────────
MSISDN_RE = re.compile(r'^\d{9,12}$')
# compiles a regular expression pattern that matches strings consisting of 9 to 12 digits. This pattern is used to validate MSISDNs (Mobile Station International Subscriber Directory Numbers).

def validate_msisdn(series: pd.Series) -> pd.Series:
    """Return boolean mask: True where MSISDN is valid (9-12 digits)."""
    return series.astype(str).str.match(MSISDN_RE)

def normalise_date(series: pd.Series) -> pd.Series:
    """Parse DD/MM/YYYY or YYYY-MM-DD and return YYYY-MM-DD strings."""
    return pd.to_datetime(series, dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

def msisdn_str(series: pd.Series) -> pd.Series:
    """Cast numeric MSISDN (stored as float by pandas) to clean integer string."""
    return series.dropna().astype(float).astype(int).astype(str)

def report(label, original, cleaned):
    removed = original - len(cleaned)
    print(f"  [{label}] {original} rows → {len(cleaned)} rows  (removed {removed})")


# ═══════════════════════════════════════════════════════════════════════════
# 1. SUBSCRIBERS
# ═══════════════════════════════════════════════════════════════════════════
print("\n── Subscribers ──────────────────────────────────────────────────────")
df = pd.read_csv(RAW["subscribers"])
n0 = len(df) 

# Step 1: Remove rows with missing MSISDN
df = df.dropna(subset=['MSISDN'])
print(f"  Null MSISDN removed: {n0 - len(df)}")

# Step 2: Cast MSISDN from float to integer string (removes the .0 suffix)
df['MSISDN'] = msisdn_str(df['MSISDN'])

# Step 3: Validate MSISDN length (9-12 digits)
valid_mask = validate_msisdn(df['MSISDN'])
invalid = (~valid_mask).sum()
print(f"  Invalid MSISDN (wrong length) removed: {invalid}")
df = df[valid_mask]

# Step 4: Standardise date
df['ActivationDate'] = normalise_date(df['ActivationDate'])

# Drop rows where date could not be parsed
before = len(df)
df = df.dropna(subset=['ActivationDate'])
print(f"  Unparseable ActivationDate removed: {before - len(df)}")

# Step 5: Remove duplicates (none expected, but defensive)
before = len(df)
df = df.drop_duplicates()
print(f"  Duplicates removed: {before - len(df)}")

report("Subscribers", n0, df)
df.to_csv(os.path.join(OUT_DIR, "subscribers_clean.csv"), index=False)

# ═══════════════════════════════════════════════════════════════════════════
# 2. CALLS
# ═══════════════════════════════════════════════════════════════════════════
print("\n── Calls ────────────────────────────────────────────────────────────")
df = pd.read_csv(RAW["calls"])
n0 = len(df)

# Step 1: Remove duplicate rows (keep first occurrence)
before = len(df)
df = df.drop_duplicates()
print(f"  Duplicates removed: {before - len(df)}")

# Step 2: Remove rows with null CallingMSISDN
before = len(df)
df = df.dropna(subset=['CallingMSISDN'])
print(f"  Null CallingMSISDN removed: {before - len(df)}")

# Step 3: Cast CallingMSISDN to string
df['CallingMSISDN'] = df['CallingMSISDN'].astype(float).astype(int).astype(str)

# Step 4: Validate CallingMSISDN
valid_mask = validate_msisdn(df['CallingMSISDN'])
invalid = (~valid_mask).sum()
print(f"  Invalid CallingMSISDN removed: {invalid}")
df = df[valid_mask]

# Step 5: Remove negative DurationSeconds (physically impossible)
before = len(df)
df = df[df['DurationSeconds'] >= 0]
print(f"  Negative DurationSeconds removed: {before - len(df)}")

# Step 6: Standardise CallDate
df['CallDate'] = normalise_date(df['CallDate'])

# Step 7: CalledMSISDN can be off-net (longer international numbers) – no strict validation
df['CalledMSISDN'] = df['CalledMSISDN'].astype(str)

report("Calls", n0, df)
df.to_csv(os.path.join(OUT_DIR, "calls_clean.csv"), index=False)


# ═══════════════════════════════════════════════════════════════════════════
# 3. SMS
# ═══════════════════════════════════════════════════════════════════════════
print("\n── SMS ──────────────────────────────────────────────────────────────")
df = pd.read_csv(RAW["sms"])
n0 = len(df)

# Step 1: Remove rows with null SMSDate (no date = unusable record)
before = len(df)
df = df.dropna(subset=['SMSDate'])
print(f"  Null SMSDate removed: {before - len(df)}")

# Step 2: Standardise date
df['SMSDate'] = normalise_date(df['SMSDate'])

# Step 3: Validate SourceMSISDN
df['SourceMSISDN'] = df['SourceMSISDN'].astype(str)
valid_mask = validate_msisdn(df['SourceMSISDN'])
invalid = (~valid_mask).sum()
print(f"  Invalid SourceMSISDN removed: {invalid}")
df = df[valid_mask]

# Step 4: Remove duplicates
before = len(df)
df = df.drop_duplicates()
print(f"  Duplicates removed: {before - len(df)}")

report("SMS", n0, df)
df.to_csv(os.path.join(OUT_DIR, "sms_clean.csv"), index=False)


# ═══════════════════════════════════════════════════════════════════════════
# 4. AIRTIME SALES
# ═══════════════════════════════════════════════════════════════════════════
print("\n── Airtime Sales ────────────────────────────────────────────────────")
df = pd.read_csv(RAW["airtime_sales"])
n0 = len(df)

# Step 1: Remove rows with null Amount
before = len(df)
df = df.dropna(subset=['Amount'])
print(f"  Null Amount removed: {before - len(df)}")

# Step 2: Remove negative Amount (invalid transactions)
before = len(df)
df = df[df['Amount'] > 0]
print(f"  Negative/zero Amount removed: {before - len(df)}")

# Step 3: Standardise date format (DD/MM/YYYY → YYYY-MM-DD)
df['PurchaseDate'] = normalise_date(df['PurchaseDate'])

# Step 4: Validate MSISDN
df['MSISDN'] = df['MSISDN'].astype(str)
valid_mask = validate_msisdn(df['MSISDN'])
invalid = (~valid_mask).sum()
print(f"  Invalid MSISDN removed: {invalid}")
df = df[valid_mask]

# Step 5: Remove duplicates
before = len(df)
df = df.drop_duplicates()
print(f"  Duplicates removed: {before - len(df)}")

report("Airtime Sales", n0, df)
df.to_csv(os.path.join(OUT_DIR, "airtime_sales_clean.csv"), index=False)


# ═══════════════════════════════════════════════════════════════════════════
# 5. INTERNET BUNDLE SALES
# ═══════════════════════════════════════════════════════════════════════════
print("\n── Internet Bundle Sales ────────────────────────────────────────────")
df = pd.read_csv(RAW["internet_bundle_sales"])
n0 = len(df)

# Step 1: Fill null BundleName with 'Unknown'
nulls = df['BundleName'].isnull().sum()
df['BundleName'] = df['BundleName'].fillna('Unknown')
print(f"  Null BundleName filled with 'Unknown': {nulls}")

# Step 2: Standardise date (already YYYY-MM-DD, but enforce via parse)
df['PurchaseDate'] = normalise_date(df['PurchaseDate'])

# Drop rows where date could not be parsed
before = len(df)
df = df.dropna(subset=['PurchaseDate'])
print(f"  Unparseable PurchaseDate removed: {before - len(df)}")

# Step 3: Validate MSISDN
df['MSISDN'] = df['MSISDN'].astype(str)
valid_mask = validate_msisdn(df['MSISDN'])
invalid = (~valid_mask).sum()
print(f"  Invalid MSISDN removed: {invalid}")
df = df[valid_mask]

# Step 4: Remove duplicates
before = len(df)
df = df.drop_duplicates()
print(f"  Duplicates removed: {before - len(df)}")

report("Internet Bundle Sales", n0, df)
df.to_csv(os.path.join(OUT_DIR, "internet_bundle_sales_clean.csv"), index=False)


# ═══════════════════════════════════════════════════════════════════════════
# 6. FIBRE SUBSCRIPTIONS
# ═══════════════════════════════════════════════════════════════════════════
print("\n── Fibre Subscriptions ──────────────────────────────────────────────")
df = pd.read_csv(RAW["fibre_subscriptions"])
n0 = len(df)

# Step 1: Fill null PackageName
nulls = df['PackageName'].isnull().sum()
df['PackageName'] = df['PackageName'].fillna('Unknown')
print(f"  Null PackageName filled with 'Unknown': {nulls}")

# Step 2: Remove negative MonthlyFee (invalid)
before = len(df)
df = df[df['MonthlyFee'] >= 0]
print(f"  Negative MonthlyFee removed: {before - len(df)}")

# Step 3: Standardise date format (DD/MM/YYYY → YYYY-MM-DD)
df['SubscriptionDate'] = normalise_date(df['SubscriptionDate'])

# Step 4: Validate MSISDN
df['MSISDN'] = df['MSISDN'].astype(str)
valid_mask = validate_msisdn(df['MSISDN'])
invalid = (~valid_mask).sum()
print(f"  Invalid MSISDN removed: {invalid}")
df = df[valid_mask]

# Step 5: Remove duplicates
before = len(df)
df = df.drop_duplicates()
print(f"  Duplicates removed: {before - len(df)}")

report("Fibre Subscriptions", n0, df)
df.to_csv(os.path.join(OUT_DIR, "fibre_subscriptions_clean.csv"), index=False)


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 60)
print("  CLEAN FILES WRITTEN TO:", OUT_DIR)
for f in sorted(os.listdir(OUT_DIR)):
    rows = len(pd.read_csv(os.path.join(OUT_DIR, f)))
    print(f"    {f:<42}  {rows:>4} rows")
print("═" * 60)
