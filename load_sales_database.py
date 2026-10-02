"""Validate cleaned sales data and load it into a SQLite database."""

from pathlib import Path
import math
import sqlite3

import pandas as pd

from clean_sales_data import ORDER_ID_PATTERN, standardize_name


INPUT_FILE = Path("data/processed/clean_sales.xlsx")
DATABASE_FILE = Path("data/database/flowbridge.db")
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "product",
    "category",
    "region",
    "quantity",
    "unit_price",
    "total_sales",
]


def validate_sales_data(sales_data: pd.DataFrame) -> pd.DataFrame:
    """Validate the cleaned workbook and return database-ready values."""
    problems = []
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in sales_data.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Clean sales data is missing required columns: {', '.join(missing_columns)}"
        )

    validated_data = sales_data[REQUIRED_COLUMNS].copy()

    order_ids = validated_data["order_id"]
    invalid_order_ids = order_ids.map(
        lambda value: not isinstance(value, str)
        or ORDER_ID_PATTERN.fullmatch(value) is None
    )
    if invalid_order_ids.any():
        problems.append("order_id values must use the format ORD-####")
    if order_ids.duplicated().any():
        problems.append("order_id values must be unique")

    parsed_dates = pd.to_datetime(validated_data["order_date"], errors="coerce")
    if parsed_dates.isna().any():
        problems.append("order_date values must be valid dates")

    for column in ("product", "category", "region"):
        values = validated_data[column]
        missing_or_blank = values.map(
            lambda value: not isinstance(value, str) or not value.strip()
        )
        if missing_or_blank.any():
            problems.append(f"{column} values must not be missing or blank")
        standardized = values.map(
            lambda value: standardize_name(value) if isinstance(value, str) else value
        )
        if not values.equals(standardized):
            problems.append(f"{column} values must be trimmed and use title case")

    quantities = pd.to_numeric(validated_data["quantity"], errors="coerce")
    invalid_quantities = (
        quantities.isna()
        | ~quantities.map(math.isfinite)
        | quantities.le(0)
        | quantities.mod(1).ne(0)
    )
    if invalid_quantities.any():
        problems.append("quantity values must be positive whole numbers")

    unit_prices = pd.to_numeric(validated_data["unit_price"], errors="coerce")
    if (
        unit_prices.isna()
        | ~unit_prices.map(math.isfinite)
        | unit_prices.le(0)
    ).any():
        problems.append("unit_price values must be positive numbers")

    total_sales = pd.to_numeric(validated_data["total_sales"], errors="coerce")
    invalid_totals = (
        total_sales.isna()
        | ~total_sales.map(math.isfinite)
        | total_sales.le(0)
    )
    mismatched_totals = ~total_sales.round(10).eq(
        (quantities * unit_prices).round(10)
    )
    if (invalid_totals | mismatched_totals).any():
        problems.append("total_sales must equal quantity multiplied by unit_price")

    if problems:
        raise ValueError("Invalid clean sales data: " + "; ".join(problems))

    validated_data["order_date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    validated_data["quantity"] = quantities.astype("int64")
    validated_data["unit_price"] = unit_prices.astype("float64")
    validated_data["total_sales"] = total_sales.astype("float64")
    return validated_data


def replace_sales_snapshot(
    sales_data: pd.DataFrame, database_file: Path = DATABASE_FILE
) -> None:
    """Replace all sales rows in one transaction and roll back on failure."""
    database_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_file)

    create_table_sql = """
        CREATE TABLE IF NOT EXISTS sales (
            order_id TEXT PRIMARY KEY,
            order_date TEXT NOT NULL,
            product TEXT NOT NULL,
            category TEXT NOT NULL,
            region TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price > 0),
            total_sales REAL NOT NULL CHECK (total_sales > 0)
        )
    """
    insert_sql = """
        INSERT INTO sales (
            order_id, order_date, product, category, region,
            quantity, unit_price, total_sales
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    records = [
        (
            str(row.order_id),
            str(row.order_date),
            str(row.product),
            str(row.category),
            str(row.region),
            int(row.quantity),
            float(row.unit_price),
            float(row.total_sales),
        )
        for row in sales_data.itertuples(index=False)
    ]

    try:
        connection.execute("BEGIN")
        connection.execute(create_table_sql)
        connection.execute("DELETE FROM sales")
        connection.executemany(insert_sql, records)
        connection.commit()
    except Exception as error:
        connection.rollback()
        raise RuntimeError(
            "Database load failed. The previous sales snapshot was preserved."
        ) from error
    finally:
        connection.close()


def print_database_summary(database_file: Path = DATABASE_FILE) -> None:
    """Print basic row and revenue information from SQLite."""
    with sqlite3.connect(database_file) as connection:
        row_count, total_revenue = connection.execute(
            "SELECT COUNT(*), COALESCE(SUM(total_sales), 0) FROM sales"
        ).fetchone()
        revenue_by_region = connection.execute(
            """
            SELECT region, SUM(total_sales)
            FROM sales
            GROUP BY region
            ORDER BY region
            """
        ).fetchall()

    print(f"Database path: {database_file.resolve()}")
    print(f"Loaded row count: {row_count}")
    print(f"Total revenue: {total_revenue:.2f}")
    print("Revenue by region:")
    for region, revenue in revenue_by_region:
        print(f"  {region}: {revenue:.2f}")


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}. Run clean_sales_data.py first."
        )

    clean_sales = pd.read_excel(INPUT_FILE, engine="openpyxl")
    validated_sales = validate_sales_data(clean_sales)
    replace_sales_snapshot(validated_sales)
    print_database_summary()


if __name__ == "__main__":
    main()
