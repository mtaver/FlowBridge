"""Clean and validate the sample sales data without changing the raw workbook."""

from pathlib import Path
import math
import re

import pandas as pd


INPUT_FILE = Path("data/raw/sample_sales.xlsx")
OUTPUT_DIRECTORY = Path("data/processed")
CLEAN_FILE = OUTPUT_DIRECTORY / "clean_sales.xlsx"
REJECTED_FILE = OUTPUT_DIRECTORY / "rejected_sales.xlsx"
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "product",
    "category",
    "region",
    "quantity",
    "unit_price",
]
ORDER_ID_PATTERN = re.compile(r"^ORD-\d{4}$")


def standardize_name(value: object) -> object:
    """Trim repeated spaces and use title case while preserving missing values."""
    if pd.isna(value):
        return value
    return " ".join(str(value).split()).title()


def rejection_reasons(row: pd.Series) -> str:
    """Return every validation problem found in one row."""
    reasons = []

    order_id = row["order_id"]
    if pd.isna(order_id) or not str(order_id).strip():
        reasons.append("order_id is missing or blank")
    elif not ORDER_ID_PATTERN.fullmatch(str(order_id)):
        reasons.append("order_id must use the format ORD-####")

    if pd.isna(row["parsed_order_date"]):
        reasons.append("order_date is missing or invalid")

    for column in ("product", "category", "region"):
        value = row[column]
        if pd.isna(value) or not str(value).strip():
            reasons.append(f"{column} is missing or blank")

    quantity = row["parsed_quantity"]
    if pd.isna(quantity) or not math.isfinite(float(quantity)):
        reasons.append("quantity must be a number")
    elif quantity <= 0 or not float(quantity).is_integer():
        reasons.append("quantity must be a positive whole number")

    unit_price = row["parsed_unit_price"]
    if pd.isna(unit_price) or not math.isfinite(float(unit_price)):
        reasons.append("unit_price must be a number")
    elif unit_price <= 0:
        reasons.append("unit_price must be positive")

    return "; ".join(reasons)


def clean_sales_data(sales_data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Remove duplicates, standardize names, and split valid and invalid rows."""
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in sales_data.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    duplicate_count = int(sales_data.duplicated().sum())
    working_data = sales_data.drop_duplicates().copy()

    for column in ("product", "category", "region"):
        working_data[column] = working_data[column].map(standardize_name)

    working_data["parsed_order_date"] = pd.to_datetime(
        working_data["order_date"], errors="coerce"
    )
    working_data["parsed_quantity"] = pd.to_numeric(
        working_data["quantity"], errors="coerce"
    )
    working_data["parsed_unit_price"] = pd.to_numeric(
        working_data["unit_price"], errors="coerce"
    )
    working_data["rejection_reason"] = working_data.apply(
        rejection_reasons, axis=1
    )

    valid_mask = working_data["rejection_reason"].eq("")

    clean_data = working_data.loc[valid_mask, REQUIRED_COLUMNS].copy()
    clean_data["order_date"] = working_data.loc[valid_mask, "parsed_order_date"]
    clean_data["quantity"] = (
        working_data.loc[valid_mask, "parsed_quantity"].astype("int64")
    )
    clean_data["unit_price"] = working_data.loc[
        valid_mask, "parsed_unit_price"
    ].astype("float64")
    clean_data["total_sales"] = clean_data["quantity"] * clean_data["unit_price"]

    rejected_columns = REQUIRED_COLUMNS + ["rejection_reason"]
    rejected_data = working_data.loc[~valid_mask, rejected_columns].copy()

    return clean_data.reset_index(drop=True), rejected_data.reset_index(drop=True), duplicate_count


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}. Run generate_sample_data.py first."
        )

    sales_data = pd.read_excel(INPUT_FILE, engine="openpyxl")
    clean_data, rejected_data, duplicate_count = clean_sales_data(sales_data)

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    clean_data.to_excel(CLEAN_FILE, index=False, engine="openpyxl")
    rejected_data.to_excel(REJECTED_FILE, index=False, engine="openpyxl")

    print(f"Input rows: {len(sales_data)}")
    print(f"Duplicates removed: {duplicate_count}")
    print(f"Valid rows: {len(clean_data)}")
    print(f"Rejected rows: {len(rejected_data)}")


if __name__ == "__main__":
    main()
