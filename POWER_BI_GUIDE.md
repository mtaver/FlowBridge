# FlowBridge Power BI Guide

This guide uses the generated `data/powerbi/sales.csv` file. It explains how to
build the first report in Power BI Desktop; the repository does not contain a
finished Power BI report file.

## 1. Create the CSV

Open PowerShell in the FlowBridge folder and run either the full refresh or just
the export:

```powershell
python refresh_data.py
python export_powerbi_data.py
```

The export command reads the current SQLite sales snapshot and replaces
`data/powerbi/sales.csv` only after a complete CSV has been written successfully.

## 2. Import the CSV

1. Open Power BI Desktop.
2. Select **Home > Get data > Text/CSV**.
3. Choose `data/powerbi/sales.csv` inside the FlowBridge project.
4. Select **Transform Data** so you can check the column types.
5. Rename the query to `sales`. All DAX below uses that exact table name.
6. Set these data types:

   - `order_id`, `product`, `category`, and `region`: **Text**
   - `order_date`: **Date**
   - `quantity`: **Whole number**
   - `unit_price` and `total_sales`: **Decimal number**

7. Select **Close & Apply**.

The numeric columns contain plain numbers, not currency symbols. FlowBridge does
not assume a currency. If your business has chosen one, you can apply its display
format later without changing the stored values.

## 3. Add the DAX calculations

On the **Modeling** tab, select **New measure** and add these measures one at a
time:

```DAX
Sales Record Count = COUNTROWS('sales')
```

```DAX
Total Quantity = SUM('sales'[quantity])
```

```DAX
Total Sales = SUM('sales'[total_sales])
```

For monthly reporting, select **New column** and add:

```DAX
Month Start = DATE(YEAR('sales'[order_date]), MONTH('sales'[order_date]), 1)
```

Set `Month Start` to the **Date** type and format it as `yyyy-MM` if you prefer a
compact label. Keeping it as a real date preserves chronological sorting.

## 4. Build the report

- Add three **Card** visuals using `Sales Record Count`, `Total Quantity`, and
  `Total Sales`.
- Add a **Clustered bar chart** with `region` on the category axis and
  `Total Sales` as the value.
- Add a **Line chart** with `Month Start` on the X-axis and `Total Sales` on the
  Y-axis.
- Add a **Table** visual with `product`, `Total Quantity`, and `Total Sales`.
- Add a **Slicer** using `region`.
- Add another **Slicer** using `order_date`; the **Between** style provides a
  useful date range control.

## 5. Refresh the report

The scheduled Python pipeline and Power BI refresh are separate actions:

1. `refresh_data.py` (including the Windows scheduled task) cleans the source,
   replaces the SQLite snapshot, and writes a new CSV.
2. Power BI Desktop does not automatically reload that changed CSV. Open the
   report and select **Home > Refresh**, then save the report.

If Power BI says it cannot find the CSV, open **Transform data > Data source
settings** and point the source to the current FlowBridge project path.
