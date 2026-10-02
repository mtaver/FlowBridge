"""Generate a reproducible Excel file containing intentionally messy sales data."""

from pathlib import Path
import random

import pandas as pd


OUTPUT_FILE = Path("data/raw/sample_sales.xlsx")
RANDOM_SEED = 42


def build_sample_data() -> pd.DataFrame:
    """Return 100 sample sales rows, including three exact duplicates."""
    random_generator = random.Random(RANDOM_SEED)

    products = [
        ("Laptop", "Electronics", 899.99),
        ("Wireless Mouse", "Electronics", 24.50),
        ("Desk Chair", "Furniture", 149.00),
        ("Notebook", "Stationery", 4.25),
        ("Coffee Mug", "Kitchen", 12.75),
    ]
    regions = ["North", "South", "East", "West"]
    start_date = pd.Timestamp("2025-01-01")

    rows = []
    for number in range(1, 98):
        product, category, unit_price = random_generator.choice(products)
        rows.append(
            {
                "order_id": f"ORD-{number:04d}",
                "order_date": start_date
                + pd.Timedelta(days=random_generator.randint(0, 89)),
                "product": product,
                "category": category,
                "region": random_generator.choice(regions),
                "quantity": random_generator.randint(1, 10),
                "unit_price": unit_price,
            }
        )

    # Intentional problems for later cleaning exercises.
    rows[4]["product"] = "  Laptop  "       # Extra spaces
    rows[11]["region"] = "north"            # Inconsistent capitalization
    rows[18]["category"] = "ELECTRONICS"    # Inconsistent capitalization
    rows[25]["product"] = None               # Missing value
    rows[32]["region"] = None                # Missing value
    rows[39]["unit_price"] = None            # Missing value
    rows[46]["quantity"] = 0                 # Invalid: zero
    rows[53]["quantity"] = -3                # Invalid: negative
    rows[60]["quantity"] = "unknown"         # Invalid: not a number
    rows[67]["category"] = " Furniture "     # Extra spaces

    # Copy complete rows to create three exact duplicates and reach 100 rows.
    rows.extend([rows[7].copy(), rows[20].copy(), rows[44].copy()])
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    sales_data = build_sample_data()
    sales_data.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")
    print(f"Created {OUTPUT_FILE} with {len(sales_data)} rows.")


if __name__ == "__main__":
    main()
