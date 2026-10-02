"""Run the FlowBridge cleaning and database-loading steps in order."""

from datetime import datetime
from pathlib import Path
import subprocess
import sys


PROJECT_DIRECTORY = Path(__file__).resolve().parent
STEPS = [
    ("cleaning step", PROJECT_DIRECTORY / "clean_sales_data.py"),
    ("database loading step", PROJECT_DIRECTORY / "load_sales_database.py"),
]


def current_time() -> str:
    """Return a readable local timestamp with its time-zone offset."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> int:
    print(f"Refresh started: {current_time()}", flush=True)

    for step_name, script_path in STEPS:
        print(f"Running {step_name}: {script_path.name}", flush=True)
        try:
            subprocess.run(
                [sys.executable, str(script_path)],
                cwd=PROJECT_DIRECTORY,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(
                f"Refresh failed during the {step_name} "
                f"({script_path.name}), exit code {error.returncode}.",
                flush=True,
            )
            print(f"Refresh ended: {current_time()}", flush=True)
            print("Refresh status: FAILURE", flush=True)
            return error.returncode if error.returncode != 0 else 1
        except OSError as error:
            print(
                f"Refresh failed during the {step_name} "
                f"({script_path.name}): {error}",
                flush=True,
            )
            print(f"Refresh ended: {current_time()}", flush=True)
            print("Refresh status: FAILURE", flush=True)
            return 1

    print(f"Refresh ended: {current_time()}", flush=True)
    print("Refresh status: SUCCESS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
