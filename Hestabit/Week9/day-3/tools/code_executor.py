from pathlib import Path
import pandas as pd


def analyze_sales_csv(csv_path: str) -> str:
    """
    Analyze a sales CSV file and return key business insights using Python + pandas.
    Required columns: date, region, product, units, unit_price.
    """
    path = Path(csv_path)
    if not path.exists():
        return f"ERROR: CSV not found: {csv_path}"
    try:
        df = pd.read_csv(path)
        required = {"date", "region", "product", "units", "unit_price"}
        missing = required - set(df.columns)
        if missing:
            return f"ERROR: Missing required columns: {sorted(missing)}"

        df["revenue"] = df["units"] * df["unit_price"]

        total_revenue = float(df["revenue"].sum())
        total_units = int(df["units"].sum())

        top_product = (
            df.groupby("product", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
            .iloc[0]
        )

        top_region = (
            df.groupby("region", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
            .iloc[0]
        )

        avg_order_value = float(df["revenue"].mean())

        highest_units_product = (
            df.groupby("product", as_index=False)["units"]
            .sum()
            .sort_values("units", ascending=False)
            .iloc[0]
        )

        lowest_revenue_region = (
            df.groupby("region", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=True)
            .iloc[0]
        )

        insights = [
            f"1. Total revenue: {total_revenue:.2f}.",
            f"2. Total units sold: {total_units}.",
            f"3. Top revenue product: {top_product['product']} "
            f"({float(top_product['revenue']):.2f}).",
            f"4. Top revenue region: {top_region['region']} "
            f"({float(top_region['revenue']):.2f}).",
            f"5. Highest volume product: {highest_units_product['product']} "
            f"({int(highest_units_product['units'])} units).",
            f"6. Average transaction revenue: {avg_order_value:.2f}.",
            f"7. Lowest revenue region: {lowest_revenue_region['region']} "
            f"({float(lowest_revenue_region['revenue']):.2f}) — needs attention.",
        ]
        return "\n".join(insights)
    except Exception as exc:
        return f"ERROR: Python analysis failed: {exc}"


def compute_top_n_products(csv_path: str, n: int = 5) -> str:
    """
    Return the top N products by total revenue from a sales CSV file.
    Defaults to top 5.
    """
    path = Path(csv_path)
    if not path.exists():
        return f"ERROR: CSV not found: {csv_path}"
    try:
        df = pd.read_csv(path)
        df["revenue"] = df["units"] * df["unit_price"]
        result = (
            df.groupby("product", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
            .head(n)
        )
        return f"TOP_{n}_PRODUCTS_BY_REVENUE:\n{result.to_string(index=False)}"
    except Exception as exc:
        return f"ERROR: Could not compute top products: {exc}"

