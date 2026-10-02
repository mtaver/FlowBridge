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

Export the current SQLite sales snapshot for Power BI:

```powershell
python export_powerbi_data.py
```

This writes `data/powerbi/sales.csv` in a stable row order. The previous CSV is
preserved if an export fails. See the beginner-friendly
[Power BI guide](POWER_BI_GUIDE.md) for import steps, DAX measures, visuals, and
report refresh instructions.

Refresh the cleaned data and database together:

```powershell
python refresh_data.py
```

With no options, the refresh command keeps its original behavior: it cleans
`data/raw/sample_sales.xlsx` and replaces the sales snapshot in SQLite. To select
a different Excel workbook explicitly, use:

```powershell
python refresh_data.py --source excel --input "C:\path\to\sales.xlsx"
```

To refresh from an API, start the local demo in one terminal:

```powershell
python demo_api_sales.py
```

Then run this command in another terminal:

```powershell
python refresh_data.py --source api --url http://127.0.0.1:8000/sales
```

API mode fetches raw records into `data/raw/api_sales.xlsx`, then uses the same
cleaner and database loader as Excel mode. Every successful refresh replaces the
current cleaned files, SQLite sales snapshot, and Power BI CSV; Excel and API
sources are not combined. The export runs only after a successful database load.
If the export then fails, the database may already contain the new snapshot while
the prior CSV is preserved. The Streamlit dashboard still reads
`data/processed/clean_sales.xlsx`, so reload the dashboard page after a
successful refresh to see updated data.

## Schedule a daily refresh on Windows

The scheduled task uses the Python executable inside this project's `.venv`, so
create the virtual environment and install `requirements.txt` before setup. In
PowerShell, register a daily refresh at 09:00 local time:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_scheduled_refresh.ps1
```

The task is named `FlowBridge Daily Refresh`. It runs only while your Windows
user is logged in, does not store a password, skips a new run if an earlier run
is still active, and runs a missed schedule when Windows makes that available.
The computer must be on and your user must be logged in for the task to run.

Run the registered task immediately:

```powershell
Start-ScheduledTask -TaskName "FlowBridge Daily Refresh"
```

Check its status, last result, and next run time:

```powershell
Get-ScheduledTask -TaskName "FlowBridge Daily Refresh"
Get-ScheduledTaskInfo -TaskName "FlowBridge Daily Refresh"
```

Each run writes timestamped output and error logs under `logs/`. To change the
daily time, run setup again with a 24-hour `HH:mm` value. For example:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup_scheduled_refresh.ps1 -DailyTime "14:30"
```

Remove only this project's scheduled task:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\remove_scheduled_refresh.ps1
```

Start the Streamlit sales dashboard:

```powershell
python -m streamlit run app.py
```

The dashboard reads `data/processed/clean_sales.xlsx` and shows sales metrics, a
regional sales chart, and the cleaned records. If the workbook is missing, the
page tells you to run the generator and cleaner. The dashboard never creates or
changes the data itself. Press `Ctrl+C` in PowerShell to stop the app.

## Fetch raw sales from the local demo API

The demo API reads the existing `data/raw/sample_sales.xlsx` workbook and serves
its 100 raw records as JSON. It listens only on your computer. In one PowerShell
terminal, start it with:

```powershell
python demo_api_sales.py
```

Leave that terminal open. In a second PowerShell terminal in the FlowBridge
folder, fetch the records:

```powershell
python fetch_api_sales.py http://127.0.0.1:8000/sales
```

The fetch command validates the JSON structure and writes
`data/raw/api_sales.xlsx`. It preserves the original values for a later cleaning
step. A failed request leaves the previous API workbook unchanged. Press `Ctrl+C`
in the first terminal to stop the demo API.

The scheduled task runs `python refresh_data.py` without source options, so it
continues to use `data/raw/sample_sales.xlsx` rather than the demo API.
