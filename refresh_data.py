"""Refresh FlowBridge from an Excel workbook or JSON API."""

import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import sys


PROJECT_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_EXCEL_FILE = PROJECT_DIRECTORY / "data/raw/sample_sales.xlsx"
API_EXCEL_FILE = PROJECT_DIRECTORY / "data/raw/api_sales.xlsx"


def current_time() -> str:
    """Return a readable local timestamp with its time-zone offset."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_step(step_name: str, command: list[str]) -> int:
    """Run one refresh stage and return its exit code."""
    print(f"Running {step_name}: {Path(command[1]).name}", flush=True)
    try:
        subprocess.run(command, cwd=PROJECT_DIRECTORY, check=True)
    except subprocess.CalledProcessError as error:
        print(
            f"Refresh failed during the {step_name}, exit code {error.returncode}.",
            flush=True,
        )
        return error.returncode if error.returncode != 0 else 1
    except OSError as error:
        print(f"Refresh failed during the {step_name}: {error}", flush=True)
        return 1

    print(f"Completed {step_name}.", flush=True)
    return 0


def parse_arguments() -> argparse.Namespace:
    """Parse and validate refresh source arguments."""
    parser = argparse.ArgumentParser(
        description="Clean sales data and replace the FlowBridge SQLite snapshot."
    )
    parser.add_argument(
        "--source",
        choices=("excel", "api"),
        default="excel",
        help="Data source (default: excel)",
    )
    parser.add_argument("--input", type=Path, help="Excel workbook path")
    parser.add_argument("--url", help="API URL returning a JSON list of sales records")
    arguments = parser.parse_args()

    if arguments.source == "api" and not arguments.url:
        parser.error("--url is required when --source api is selected")
    if arguments.source == "api" and arguments.input:
        parser.error("--input cannot be used with --source api")
    if arguments.source == "excel" and arguments.url:
        parser.error("--url can only be used with --source api")

    return arguments


def main() -> int:
    arguments = parse_arguments()
    print(f"Refresh started: {current_time()}", flush=True)
    print(f"Selected source: {arguments.source}", flush=True)

    if arguments.source == "api":
        steps = [
            (
                "API fetch step",
                [
                    sys.executable,
                    str(PROJECT_DIRECTORY / "fetch_api_sales.py"),
                    arguments.url,
                ],
            )
        ]
        input_file = API_EXCEL_FILE
    else:
        input_file = arguments.input or DEFAULT_EXCEL_FILE
        input_file = input_file.expanduser()
        if not input_file.is_absolute():
            input_file = input_file.resolve()
        steps = []

    steps.extend(
        [
            (
                "cleaning step",
                [
                    sys.executable,
                    str(PROJECT_DIRECTORY / "clean_sales_data.py"),
                    "--input",
                    str(input_file),
                ],
            ),
            (
                "database loading step",
                [sys.executable, str(PROJECT_DIRECTORY / "load_sales_database.py")],
            ),
            (
                "Power BI export step",
                [sys.executable, str(PROJECT_DIRECTORY / "export_powerbi_data.py")],
            ),
        ]
    )

    for step_name, command in steps:
        exit_code = run_step(step_name, command)
        if exit_code != 0:
            print(f"Refresh ended: {current_time()}", flush=True)
            print("Refresh status: FAILURE", flush=True)
            return exit_code

    print(f"Refresh ended: {current_time()}", flush=True)
    print("Refresh status: SUCCESS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
