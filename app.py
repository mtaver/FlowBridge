"""Small Streamlit dashboard for the cleaned FlowBridge sales data."""

from pathlib import Path

import pandas as pd
import streamlit as st


CLEAN_FILE = Path("data/processed/clean_sales.xlsx")


def load_sales_data(file_path: Path = CLEAN_FILE) -> pd.DataFrame:
    """Read the cleaned sales workbook without changing it."""
    return pd.read_excel(file_path, engine="openpyxl")


def calculate_metrics(sales_data: pd.DataFrame) -> tuple[int, int, float]:
    """Return the valid-record count, total quantity, and total sales."""
    return (
        len(sales_data),
        int(sales_data["quantity"].sum()),
        float(sales_data["total_sales"].sum()),
    )


def main() -> None:
    st.set_page_config(page_title="FlowBridge Sales Dashboard", layout="wide")
    st.title("FlowBridge — Sales Dashboard")

    if not CLEAN_FILE.exists():
        st.warning("The cleaned sales workbook is missing.")
        st.write("Run these commands in PowerShell, then reload the dashboard:")
        st.code(
            "python generate_sample_data.py\npython clean_sales_data.py",
            language="powershell",
        )
        return

    try:
        sales_data = load_sales_data()
        record_count, total_quantity, total_sales = calculate_metrics(sales_data)
    except Exception as error:
        st.error(f"Could not read the cleaned sales workbook: {error}")
        return

    metric_columns = st.columns(3)
    metric_columns[0].metric("Valid records", f"{record_count:,}")
    metric_columns[1].metric("Total quantity", f"{total_quantity:,}")
    metric_columns[2].metric("Total sales", f"${total_sales:,.2f}")

    st.subheader("Total sales by region")
    regional_sales = (
        sales_data.groupby("region", as_index=False)["total_sales"]
        .sum()
        .sort_values("region")
    )
    st.bar_chart(regional_sales, x="region", y="total_sales")

    st.subheader("Cleaned sales records")
    st.dataframe(sales_data, hide_index=True)


if __name__ == "__main__":
    main()
