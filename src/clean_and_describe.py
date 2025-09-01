import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        # For .xls you may need: pip install xlrd
        try:
            return pd.read_excel(path, sheet_name="Orders")
        except Exception:
            return pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Dates
    for c in df.columns:
        if "date" in c.lower():
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # Numerics
    for c in ["Sales", "Profit", "Discount", "Quantity", "Postal Code"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Strings
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()

    # Duplicates
    df = df.drop_duplicates()

    # Drop rows missing essential fields
    essential = [c for c in ["Order Date", "Sales", "Profit"] if c in df.columns]
    if essential:
        df = df.dropna(subset=essential)

    return df


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "Order Date" in df.columns:
        df["OrderYear"] = df["Order Date"].dt.year
        df["OrderMonth"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()

    if {"Order Date", "Ship Date"}.issubset(df.columns):
        df["ShipDelayDays"] = (df["Ship Date"] - df["Order Date"]).dt.days

    if {"Sales", "Profit"}.issubset(df.columns):
        df["ProfitMargin"] = np.where(df["Sales"] != 0, df["Profit"] / df["Sales"], np.nan)

    return df


def compute_kpis(df: pd.DataFrame) -> dict:
    kpis = {}
    if "Sales" in df.columns:
        kpis["total_sales"] = float(df["Sales"].sum())
    if "Profit" in df.columns:
        kpis["total_profit"] = float(df["Profit"].sum())
    if {"Sales", "Profit"}.issubset(df.columns) and df["Sales"].sum() != 0:
        kpis["overall_profit_margin"] = float(df["Profit"].sum() / df["Sales"].sum())
    if "Order Date" in df.columns and df["Order Date"].notna().any():
        kpis["date_range"] = {
            "min": df["Order Date"].min().strftime("%Y-%m-%d"),
            "max": df["Order Date"].max().strftime("%Y-%m-%d"),
        }
    return kpis


def describe_data(df: pd.DataFrame):
    desc_numeric = df.select_dtypes(include=[np.number]).describe().T
    cat_df = df.select_dtypes(exclude=[np.number])
    desc_categorical = pd.DataFrame({"n_unique": cat_df.nunique()})
    if not cat_df.empty:
        desc_categorical["top"] = cat_df.mode().iloc[0]
    return desc_numeric, desc_categorical


def aggregates(df: pd.DataFrame):
    group_tables = {}

    def aggr(cols):
        return (
            df.groupby(cols)[["Sales", "Profit"]]
            .sum()
            .assign(ProfitMargin=lambda x: np.where(x["Sales"] != 0, x["Profit"] / x["Sales"], np.nan))
            .sort_values("Sales", ascending=False)
        )

    if {"Category", "Sales", "Profit"}.issubset(df.columns):
        group_tables["by_category"] = aggr(["Category"])
    if {"Sub-Category", "Sales", "Profit"}.issubset(df.columns):
        group_tables["by_subcategory"] = aggr(["Sub-Category"])
    if {"Region", "Sales", "Profit"}.issubset(df.columns):
        group_tables["by_region"] = aggr(["Region"])
    if {"State", "Sales", "Profit"}.issubset(df.columns):
        group_tables["by_state"] = aggr(["State"])

    monthly_sales = None
    if {"OrderMonth", "Sales"}.issubset(df.columns):
        monthly_sales = (
            df.groupby("OrderMonth")["Sales"]
            .sum()
            .reset_index()
            .sort_values("OrderMonth")
        )

    top_products = None
    if {"Product Name", "Sales", "Profit"}.issubset(df.columns):
        top_products = (
            df.groupby("Product Name")[["Sales", "Profit"]]
            .sum()
            .assign(ProfitMargin=lambda x: np.where(x["Sales"] != 0, x["Profit"] / x["Sales"], np.nan))
            .sort_values("Sales", ascending=False)
            .head(10)
            .reset_index()
        )

    return group_tables, monthly_sales, top_products


def charts(group_tables: dict, monthly_sales: pd.DataFrame | None, out_dir: Path):
    # Sales by Category
    if "by_category" in group_tables:
        plt.figure()
        group_tables["by_category"]["Sales"].plot(kind="bar", title="Sales by Category")
        plt.ylabel("Sales")
        plt.xlabel("Category")
        plt.tight_layout()
        plt.savefig(out_dir / "sales_by_category.png")
        plt.close()

    # Monthly Sales
    if monthly_sales is not None and not monthly_sales.empty:
        plt.figure()
        plt.plot(monthly_sales["OrderMonth"], monthly_sales["Sales"])
        plt.title("Monthly Sales")
        plt.ylabel("Sales")
        plt.xlabel("Month")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(out_dir / "monthly_sales.png")
        plt.close()


def save_artifacts(
    df: pd.DataFrame,
    kpis: dict,
    desc_numeric: pd.DataFrame,
    desc_categorical: pd.DataFrame,
    group_tables: dict,
    monthly_sales: pd.DataFrame | None,
    top_products: pd.DataFrame | None,
    out_dir: Path,
):

    # Core
    df.to_csv(out_dir / "superstore_clean.csv", index=False)
    desc_numeric.to_csv(out_dir / "desc_numeric.csv")
    desc_categorical.to_csv(out_dir / "desc_categorical.csv")
    (out_dir / "kpi_summary.json").write_text(json.dumps(kpis, indent=2), encoding="utf-8")

    # Aggregates
    for name, t in group_tables.items():
        t.to_csv(out_dir / f"group_{name}.csv")

    if monthly_sales is not None and not monthly_sales.empty:
        monthly_sales.to_csv(out_dir / "monthly_sales.csv", index=False)
    if top_products is not None and not top_products.empty:
        top_products.to_csv(out_dir / "top10_products.csv", index=False)

    # Data dictionary
    data_dict = pd.DataFrame(
        {
            "column": df.columns,
            "dtype": df.dtypes.astype(str),
            "n_missing": df.isna().sum(),
            "sample_value": [df[c].dropna().iloc[0] if df[c].notna().any() else None for c in df.columns],
        }
    )
    data_dict.to_csv(out_dir / "data_dictionary.csv", index=False)

    # README
    readme = """# Superstore — Cleaning & Descriptive Statistics

This folder contains outputs generated by `src/clean_and_describe.py`.

## Files
- superstore_clean.csv — cleaned dataset
- desc_numeric.csv, desc_categorical.csv — descriptive stats
- group_by_category.csv, group_by_subcategory.csv, group_by_region.csv, group_by_state.csv — aggregates
- monthly_sales.csv — monthly trend (if dates present)
- top10_products.csv — top products by sales
- kpi_summary.json — key KPIs
- data_dictionary.csv — column dictionary
- sales_by_category.png, monthly_sales.png — quick charts
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Clean Superstore data and compute descriptive statistics.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "data" / "US Superstore data - Orders.csv"),
        help="Path to input CSV/XLSX/XLS (default: data/US Superstore data - Orders.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "outputs"),
        help="Output directory (default: outputs/)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    out_dir = Path(args.output)

    df_raw = load_data(input_path)
    df = basic_clean(df_raw)
    df = feature_engineering(df)

    kpis = compute_kpis(df)
    desc_numeric, desc_categorical = describe_data(df)
    group_tables, monthly_sales, top_products = aggregates(df)

    out_dir.mkdir(parents=True, exist_ok=True)

    charts(group_tables, monthly_sales, out_dir)
    save_artifacts(df, kpis, desc_numeric, desc_categorical, group_tables, monthly_sales, top_products, out_dir)

    # Optional console preview
    print("Rows:", len(df), "Cols:", df.shape[1])
    print("KPIs:", json.dumps(kpis, indent=2))
    if "by_category" in group_tables:
        print("\nSales by Category (top):")
        print(group_tables["by_category"].head())
    if top_products is not None:
        print("\nTop 10 Products (by Sales):")
        print(top_products.head())


if __name__ == "__main__":
    main()
