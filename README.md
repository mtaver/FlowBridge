# FlowBridge

FlowBridge is a beginner-friendly data project. It generates a small,
intentionally messy Excel sales dataset, inspects it, and creates separate clean
and rejected datasets without changing the raw file.

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

## Cleaning rules

The cleaning script removes exact duplicate rows first. It then trims extra or
repeated spaces and converts `product`, `category`, and `region` names to title
case.

A row is accepted only when:

- `order_id` uses the format `ORD-####`, such as `ORD-0001`.
- `order_date` contains a valid date.
- `product`, `category`, and `region` are not missing or blank.
- `quantity` is a positive whole number.
- `unit_price` is a positive number.

Valid rows receive a `total_sales` column calculated as `quantity × unit_price`
and are saved to `data/processed/clean_sales.xlsx`. Invalid rows are saved to
`data/processed/rejected_sales.xlsx`. Its `rejection_reason` column lists every
problem found in that row. Missing values are not guessed or filled in.

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

Clean and validate the workbook:

```powershell
py clean_sales_data.py
```

Run the generator before the cleaner whenever you want to recreate the original
sample. The cleaner can be run repeatedly and will replace only the generated
files in `data/processed`; it never changes `data/raw/sample_sales.xlsx`.

Load the clean sales data into SQLite:

```powershell
py load_sales_database.py
```

The loader validates the clean workbook before opening the database. A successful
run creates `data/database/flowbridge.db`, replaces the current `sales` table
snapshot, and prints the loaded row count and total sales. Running it again
does not append duplicate rows. If loading fails, the transaction is rolled back
and the previous database records are preserved.

Start the Streamlit sales dashboard:

```powershell
python -m streamlit run app.py
```

The dashboard reads `data/processed/clean_sales.xlsx` and shows sales metrics, a
regional sales chart, and the cleaned records. If the workbook is missing, the
page tells you to run the generator and cleaner. The dashboard never creates or
changes the data itself. Press `Ctrl+C` in PowerShell to stop the app.
