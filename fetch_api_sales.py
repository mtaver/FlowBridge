"""Fetch raw sales records from an API and save them as an Excel workbook."""

import argparse
import os
from pathlib import Path
import tempfile

import pandas as pd
import requests


PROJECT_DIRECTORY = Path(__file__).resolve().parent
OUTPUT_FILE = PROJECT_DIRECTORY / "data/raw/api_sales.xlsx"
REQUEST_TIMEOUT_SECONDS = 15
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "product",
    "category",
    "region",
    "quantity",
    "unit_price",
]


def validate_records(payload: object) -> list[dict]:
    """Validate the JSON structure without cleaning any field values."""
    if not isinstance(payload, list):
        raise ValueError("JSON response must be a list of sales records.")
    if not payload:
        raise ValueError("JSON response contains no sales records.")

    validated_records = []
    for record_number, record in enumerate(payload, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Record {record_number} must be a JSON object.")

        missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in record
        ]
        if missing_columns:
            raise ValueError(
                f"Record {record_number} is missing required columns: "
                f"{', '.join(missing_columns)}"
            )

        validated_records.append(
            {column: record[column] for column in REQUIRED_COLUMNS}
        )

    return validated_records


def save_records(records: list[dict], output_file: Path = OUTPUT_FILE) -> None:
    """Write records to a temporary workbook, then atomically replace output."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            prefix="api_sales_",
            suffix=".xlsx",
            dir=output_file.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        sales_data = pd.DataFrame.from_records(records, columns=REQUIRED_COLUMNS)
        sales_data.to_excel(temporary_path, index=False, engine="openpyxl")
        os.replace(temporary_path, output_file)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def fetch_records(api_url: str) -> list[dict]:
    """Fetch and validate sales records from one API URL."""
    try:
        response = requests.get(api_url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.Timeout as error:
        raise RuntimeError(
            f"API request timed out after {REQUEST_TIMEOUT_SECONDS} seconds."
        ) from error
    except requests.ConnectionError as error:
        raise RuntimeError(f"Could not connect to the API: {api_url}") from error
    except requests.RequestException as error:
        raise RuntimeError(f"API request failed: {error}") from error

    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise RuntimeError(
            f"API returned HTTP {response.status_code}: {response.reason}"
        ) from error

    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError("API response is not valid JSON.") from error

    return validate_records(payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch raw FlowBridge sales records from a JSON API."
    )
    parser.add_argument("api_url", help="URL returning a JSON list of sales records")
    arguments = parser.parse_args()

    try:
        records = fetch_records(arguments.api_url)
        save_records(records)
    except (RuntimeError, ValueError, OSError) as error:
        print(f"API ingestion failed: {error}")
        return 1

    print(f"Saved {len(records)} raw API records to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
