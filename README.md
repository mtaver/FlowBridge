# FlowBridge

FlowBridge is a beginner-friendly data project. This first step generates a small,
intentionally messy Excel sales dataset and inspects it without changing the file.

## Intentional data problems

The generated workbook contains 100 rows and these deliberate issues for future
cleaning exercises:

- Three exact duplicate rows.
- Missing values in `product`, `region`, and `unit_price`.
- Extra spaces around some `product` and `category` values.
- Inconsistent capitalization in some `region` and `category` values.
- Invalid `quantity` values: zero, a negative number, and the text `unknown`.

The inspection script only reads the workbook. It does not edit or overwrite the
original Excel data.

## Install on Windows

First install Python 3.10 or newer from [python.org](https://www.python.org/downloads/windows/).
During setup, select **Add Python to PATH**. Then open PowerShell in this project
folder and confirm Python is available:

```powershell
py --version
```

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
py -m pip install -r requirements.txt
```

If PowerShell blocks activation, you can skip activation and use
`.\.venv\Scripts\python.exe` instead of `py` in the commands below.

## Run

Generate the reproducible sample workbook:

```powershell
py generate_sample_data.py
```

This creates `data/raw/sample_sales.xlsx`. Running the generator again recreates
the same sample data.

Inspect the workbook:

```powershell
py inspect_sales_data.py
```

The inspection prints the row count, column names, first five rows,
missing-value counts, and exact duplicate-row count.
