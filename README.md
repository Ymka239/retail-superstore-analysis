# Retail Superstore — Data Cleaning & Descriptive Statistics

This project analyzes the **Superstore Sales dataset** (from Kaggle) as part of a Retail/Store analytics case study.  
The focus is on cleaning the raw data, generating descriptive statistics, and preparing outputs for BI tools and presentations.

---

## 📂 Project Structure
retail-superstore/

├─ data/ # input dataset
│ └─ US Superstore data - Orders.csv
├─ outputs/ # generated artifacts
│ ├─ superstore_clean.csv
│ ├─ desc_numeric.csv
│ ├─ desc_categorical.csv
│ ├─ group_by_category.csv
│ ├─ group_by_subcategory.csv
│ ├─ group_by_region.csv
│ ├─ group_by_state.csv
│ ├─ monthly_sales.csv
│ ├─ top10_products.csv
│ ├─ kpi_summary.json
│ ├─ data_dictionary.csv
│ ├─ sales_by_category.png
│ ├─ monthly_sales.png
│ └─ README.md
├─ src/
│ └─ clean_and_describe.py
└─ requirements.txt


---

## 🚀 How to Run
1. Clone this repo and install requirements:
   ```bash
   pip install -r requirements.txt
2. Place the dataset in the data/ folder (default name: US Superstore data - Orders.csv).

3. Run the script:
   ```bash
   python src/clean_and_describe.py
4. Check the outputs/ folder for generated files.

## 📊 Outputs

superstore_clean.csv — cleaned dataset

desc_numeric.csv / desc_categorical.csv — descriptive statistics

group_by_category.csv / group_by_subcategory.csv / group_by_region.csv / group_by_state.csv — aggregated summaries

monthly_sales.csv — monthly sales trend

top10_products.csv — top 10 products by sales

kpi_summary.json — key KPIs (total sales, profit, margin, date range)

data_dictionary.csv — column metadata

sales_by_category.png / monthly_sales.png — quick charts

## 💡 Business Questions

Which category and sub-category generate the most sales and profit?

Which region or state underperforms by profit margin?

What are the top products by sales and profit?

Do shipping delays correlate with profitability?

What is the monthly trend of sales — are there seasonal peaks?

## 🛠 Requirements

Python 3.10+

pandas, numpy, matplotlib