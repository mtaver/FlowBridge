"""Read and inspect the sample sales workbook without changing it."""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/raw/sample_sales.xlsx")


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}. Run generate_sample_data.py first."
        )

    # Reading into memory does not modify the original Excel workbook.
    sales_data = pd.read_excel(INPUT_FILE, engine="openpyxl")

    print(f"Row count: {len(sales_data)}")
    print("\nColumn names:")
    print(sales_data.columns.tolist())
    print("\nFirst five rows:")
    print(sales_data.head().to_string(index=False))
    print("\nMissing-value counts:")
    print(sales_data.isna().sum().to_string())
    print(f"\nExact duplicate-row count: {sales_data.duplicated().sum()}")


if __name__ == "__main__":
    main()
