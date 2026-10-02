"""Serve the sample FlowBridge sales records as JSON on localhost."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


PROJECT_DIRECTORY = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_DIRECTORY / "data/raw/sample_sales.xlsx"
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "product",
    "category",
    "region",
    "quantity",
    "unit_price",
]


def json_value(value: object, column: str) -> object:
    """Convert spreadsheet values into JSON-safe values."""
    if pd.isna(value):
        return None
    if column == "order_date":
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    if hasattr(value, "item"):
        return value.item()
    return value


def load_records() -> list[dict]:
    """Read all sample rows and preserve their raw values for the API."""
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {SOURCE_FILE}. Run generate_sample_data.py first."
        )

    sales_data = pd.read_excel(SOURCE_FILE, engine="openpyxl")
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in sales_data.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Sample workbook is missing columns: {', '.join(missing_columns)}"
        )

    return [
        {
            column: json_value(row[column], column)
            for column in REQUIRED_COLUMNS
        }
        for row in sales_data.to_dict(orient="records")
    ]


class SalesApiHandler(BaseHTTPRequestHandler):
    """Return sample sales data from the /sales endpoint."""

    records: list[dict] = []

    def do_GET(self) -> None:
        if urlparse(self.path).path != "/sales":
            self.send_error(404, "Use the /sales endpoint")
            return

        response_body = json.dumps(self.records, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, format: str, *arguments: object) -> None:
        print(f"API request: {format % arguments}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local FlowBridge demo API.")
    parser.add_argument("--port", type=int, default=8000, help="Local port (default: 8000)")
    arguments = parser.parse_args()

    SalesApiHandler.records = load_records()
    server = ThreadingHTTPServer(("127.0.0.1", arguments.port), SalesApiHandler)
    print(f"Serving {len(SalesApiHandler.records)} records at http://127.0.0.1:{arguments.port}/sales")
    print("Press Ctrl+C to stop the demo API.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping the demo API.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
