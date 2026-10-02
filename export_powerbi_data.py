"""Export the FlowBridge SQLite sales snapshot for Power BI."""

from pathlib import Path
import os
import sqlite3
import tempfile

import pandas as pd


PROJECT_DIRECTORY = Path(__file__).resolve().parent
DATABASE_FILE = PROJECT_DIRECTORY / "data/database/flowbridge.db"
OUTPUT_FILE = PROJECT_DIRECTORY / "data/powerbi/sales.csv"
SALES_COLUMNS = [
    "order_id",
    "order_date",
    "product",
    "category",
    "region",
    "quantity",
    "unit_price",
    "total_sales",
]


def read_sales(database_file: Path) -> pd.DataFrame:
    """Read and validate the sales table without creating a database."""
    database_file = database_file.resolve()
    if not database_file.is_file():
        raise FileNotFoundError(f"Database not found: {database_file}")

    database_uri = f"{database_file.as_uri()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    try:
        table_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'sales'"
        ).fetchone()
        if table_exists is None:
            raise ValueError(f"Sales table not found in database: {database_file}")

        column_list = ", ".join(SALES_COLUMNS)
        sales = pd.read_sql_query(
            f"SELECT {column_list} FROM sales ORDER BY order_id", connection
        )
    finally:
        connection.close()

    if list(sales.columns) != SALES_COLUMNS:
        raise ValueError("The sales table does not contain the required columns.")

    parsed_dates = pd.to_datetime(sales["order_date"], errors="coerce")
    if parsed_dates.isna().any():
        raise ValueError("The sales table contains an invalid order_date.")
    sales["order_date"] = parsed_dates.dt.strftime("%Y-%m-%d")

    for column in ("quantity", "unit_price", "total_sales"):
        converted = pd.to_numeric(sales[column], errors="coerce")
        if converted.isna().any():
            raise ValueError(f"The sales table contains a nonnumeric {column} value.")
        sales[column] = converted

    if not (sales["quantity"] % 1 == 0).all():
        raise ValueError("The sales table contains a non-whole quantity.")
    sales["quantity"] = sales["quantity"].astype("int64")
    return sales


def export_sales(
    database_file: Path = DATABASE_FILE, output_file: Path = OUTPUT_FILE
) -> tuple[int, float]:
    """Atomically export the SQLite sales snapshot to a deterministic CSV."""
    sales = read_sales(database_file)
    output_file = output_file.resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=f".{output_file.stem}-",
            suffix=".tmp",
            dir=output_file.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            sales.to_csv(temporary_file, index=False, lineterminator="\n")

        os.replace(temporary_path, output_file)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return len(sales), float(sales["total_sales"].sum())


def main() -> int:
    try:
        row_count, total_sales = export_sales()
    except (FileNotFoundError, OSError, sqlite3.Error, ValueError) as error:
        print(f"Power BI export failed: {error}")
        return 1

    print(f"Power BI CSV: {OUTPUT_FILE.resolve()}")
    print(f"Exported record count: {row_count}")
    print(f"Exported total sales: {total_sales:,.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
