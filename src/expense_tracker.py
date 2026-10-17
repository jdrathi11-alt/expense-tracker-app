"""Core data pipeline for a small, synthetic expense tracker.

The functions in this module deliberately use ordinary pandas DataFrames so a
student can inspect each step in a notebook or from the command line:

1. generate synthetic rows
2. clean the raw rows
3. add helpful time features
4. calculate summaries and KPIs
5. create charts and save reusable output files
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib

# The CLI may run on a server without a display.  Agg keeps plotting headless.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


CORE_COLUMNS = ("date", "category", "amount")
STANDARD_COLUMNS = (
    "expense_id",
    "date",
    "category",
    "description",
    "amount",
    "payment_method",
    "merchant",
)
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CATEGORIES = [
    "Housing",
    "Food",
    "Transportation",
    "Utilities",
    "Entertainment",
    "Healthcare",
    "Shopping",
    "Travel",
    "Education",
    "Other",
]
PAYMENT_METHODS = ["Card", "Cash", "Bank Transfer", "Digital Wallet"]

# These are illustrative monthly budgets, not financial advice.  They make the
# budget part of the demo easy to understand and deterministic.
MONTHLY_BUDGETS = {
    "Housing": 1_400.00,
    "Food": 500.00,
    "Transportation": 250.00,
    "Utilities": 250.00,
    "Entertainment": 200.00,
    "Healthcare": 250.00,
    "Shopping": 350.00,
    "Travel": 300.00,
    "Education": 150.00,
    "Other": 200.00,
}
DEFAULT_MONTHLY_BUDGET = 200.00

CATEGORY_PROBABILITIES = np.array(
    [0.08, 0.24, 0.14, 0.08, 0.09, 0.05, 0.12, 0.05, 0.05, 0.10]
)
CATEGORY_SCALES = {
    "Housing": 900.00,
    "Food": 35.00,
    "Transportation": 28.00,
    "Utilities": 95.00,
    "Entertainment": 45.00,
    "Healthcare": 85.00,
    "Shopping": 70.00,
    "Travel": 180.00,
    "Education": 70.00,
    "Other": 30.00,
}
CATEGORY_DESCRIPTIONS = {
    "Housing": ["Rent payment", "Home supplies", "Repair service"],
    "Food": ["Grocery shopping", "Lunch", "Coffee", "Dinner"],
    "Transportation": ["Fuel", "Bus fare", "Ride share", "Parking"],
    "Utilities": ["Electricity bill", "Internet bill", "Water bill", "Phone bill"],
    "Entertainment": ["Movie ticket", "Streaming subscription", "Concert"],
    "Healthcare": ["Pharmacy", "Doctor visit", "Health supplies"],
    "Shopping": ["Clothing", "Household item", "Online order"],
    "Travel": ["Hotel", "Train ticket", "Flight", "Travel activity"],
    "Education": ["Book", "Course fee", "Learning supplies"],
    "Other": ["Gift", "Donation", "Miscellaneous"],
}
CATEGORY_MERCHANTS = {
    "Housing": ["Home Services", "Apartment Management", "Hardware Store"],
    "Food": ["Fresh Market", "City Cafe", "Neighborhood Restaurant", "Corner Bakery"],
    "Transportation": ["Metro Transit", "Fuel Station", "RideNow", "City Parking"],
    "Utilities": ["Power Company", "NetConnect", "Water Works", "Mobile Provider"],
    "Entertainment": ["Cinema House", "StreamFlix", "Music Hall"],
    "Healthcare": ["Community Pharmacy", "Health Clinic", "Wellness Store"],
    "Shopping": ["General Store", "Style Shop", "Market Place"],
    "Travel": ["Travel Hub", "Rail Network", "StayEasy", "Airline Co"],
    "Education": ["Book Corner", "Learning Center", "Course Platform"],
    "Other": ["Local Shop", "Community Center", "Various"],
}


def _require_dataframe(df: pd.DataFrame, function_name: str) -> None:
    """Raise a clear error when a public function receives the wrong type."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{function_name} expects a pandas DataFrame")


def _require_columns(df: pd.DataFrame, required: Iterable[str], function_name: str) -> None:
    missing = sorted(set(required).difference(df.columns))
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"{function_name} requires columns: {names}")


def _round_currency(value: Any) -> float:
    """Return a normal Python float rounded to two currency-friendly decimals."""
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value), 2)


def _currency(value: Any) -> str:
    return f"${_round_currency(value):,.2f}"


def _path_and_create(directory: str | Path) -> Path:
    path = Path(directory).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ordered_columns(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [column for column in STANDARD_COLUMNS if column in df.columns]
    extras = [column for column in df.columns if column not in preferred]
    return df.loc[:, preferred + extras]


def generate_synthetic_expenses(
    n_rows: int = 720,
    start_date: str = "2025-01-01",
    seed: int = 42,
    include_quality_issues: bool = True,
) -> pd.DataFrame:
    """Generate deterministic, realistic-looking synthetic expense records.

    ``include_quality_issues`` deliberately adds a few bad values and one
    duplicate ID to make the cleaning step useful in a classroom exercise.
    The returned row count remains exactly ``n_rows``.
    """
    if isinstance(n_rows, bool) or not isinstance(n_rows, (int, np.integer)):
        raise TypeError("n_rows must be a non-negative integer")
    if n_rows < 0:
        raise ValueError("n_rows must be a non-negative integer")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")

    try:
        first_date = pd.Timestamp(start_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("start_date must be a valid date") from exc
    if pd.isna(first_date):
        raise ValueError("start_date must be a valid date")

    rng = np.random.default_rng(int(seed))
    if n_rows == 0:
        return pd.DataFrame(
            {
                "expense_id": pd.Series(dtype="string"),
                "date": pd.Series(dtype="datetime64[ns]"),
                "category": pd.Series(dtype="string"),
                "description": pd.Series(dtype="string"),
                "amount": pd.Series(dtype="float64"),
                "payment_method": pd.Series(dtype="string"),
                "merchant": pd.Series(dtype="string"),
            }
        )

    category_values = rng.choice(CATEGORIES, size=n_rows, p=CATEGORY_PROBABILITIES)
    dates = first_date + pd.to_timedelta(rng.integers(0, 365, size=n_rows), unit="D")
    amounts = np.array(
        [
            np.clip(
                rng.lognormal(mean=np.log(CATEGORY_SCALES[category]), sigma=0.42),
                2.00,
                5_000.00,
            )
            for category in category_values
        ],
        dtype=float,
    )
    amounts = np.round(amounts, 2)
    descriptions = [
        rng.choice(CATEGORY_DESCRIPTIONS[category]) for category in category_values
    ]
    merchants = [rng.choice(CATEGORY_MERCHANTS[category]) for category in category_values]
    payment_methods = rng.choice(
        PAYMENT_METHODS,
        size=n_rows,
        p=np.array([0.53, 0.15, 0.17, 0.15]),
    )

    expenses = pd.DataFrame(
        {
            "expense_id": [f"EXP-{index:05d}" for index in range(1, n_rows + 1)],
            "date": pd.to_datetime(dates),
            "category": category_values,
            "description": descriptions,
            "amount": amounts,
            "payment_method": payment_methods,
            "merchant": merchants,
        }
    )

    if include_quality_issues:
        # A duplicate valid row is useful for demonstrating deduplication.
        if n_rows >= 3:
            expenses.loc[1] = expenses.loc[2].copy()
        # Keep dates as a datetime column by using NaT rather than a text date.
        if n_rows >= 2:
            expenses.loc[0, "amount"] = -abs(float(expenses.loc[0, "amount"]))
        if n_rows >= 4:
            expenses.loc[3, "category"] = None
        if n_rows >= 5:
            expenses.loc[4, "date"] = pd.NaT

    expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce").round(2)
    return expenses


def clean_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """Clean an expense DataFrame without mutating the caller's object.

    The minimum input contract is ``date``, ``category`` and ``amount``.
    Friendly defaults are supplied for descriptive columns so small student
    examples do not need to provide every generated column.
    """
    _require_dataframe(df, "clean_expenses")
    _require_columns(df, CORE_COLUMNS, "clean_expenses")
    cleaned = df.copy(deep=True)

    if "expense_id" not in cleaned.columns:
        cleaned.insert(0, "expense_id", [f"EXP-{index:05d}" for index in range(1, len(cleaned) + 1)])
    else:
        ids = cleaned["expense_id"].copy()
        missing_ids = ids.isna() | ids.astype("string").str.strip().eq("")
        if missing_ids.any():
            ids = ids.astype(object)
            existing_ids = set(ids.loc[~missing_ids].astype("string"))
            next_number = 1
            for position in np.flatnonzero(missing_ids.to_numpy()):
                candidate = f"EXP-{next_number:05d}"
                while candidate in existing_ids:
                    next_number += 1
                    candidate = f"EXP-{next_number:05d}"
                ids.iloc[position] = candidate
                existing_ids.add(candidate)
                next_number += 1
        cleaned["expense_id"] = ids

    defaults = {
        "description": "Unspecified",
        "payment_method": "Unknown",
        "merchant": "Unknown",
    }
    for column, default in defaults.items():
        if column not in cleaned.columns:
            cleaned[column] = default
        else:
            values = cleaned[column].astype("string").str.strip()
            cleaned[column] = values.replace({"": pd.NA}).fillna(default)

    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["category"] = cleaned["category"].astype("string").str.strip()
    cleaned["category"] = cleaned["category"].replace({"": pd.NA})
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")

    valid = (
        cleaned["date"].notna()
        & cleaned["category"].notna()
        & cleaned["amount"].notna()
        & np.isfinite(cleaned["amount"].astype(float))
        & (cleaned["amount"] > 0)
    )
    cleaned = cleaned.loc[valid].copy()
    cleaned["amount"] = cleaned["amount"].round(2)
    cleaned = cleaned.loc[cleaned["amount"] > 0].copy()

    # IDs catch generated duplicates.  The second check catches exact duplicate
    # records in hand-built input while preserving two legitimate transactions
    # that happen to share the same date, amount, and category but have
    # different descriptions.
    cleaned = cleaned.drop_duplicates(subset=["expense_id"], keep="first")
    record_columns = [column for column in cleaned.columns if column != "expense_id"]
    if record_columns:
        cleaned = cleaned.drop_duplicates(subset=record_columns, keep="first")
    cleaned = cleaned.sort_values("date", kind="stable").reset_index(drop=True)
    return _ordered_columns(cleaned)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar features used by summaries and charts."""
    _require_dataframe(df, "add_features")
    _require_columns(df, CORE_COLUMNS, "add_features")
    featured = df.copy(deep=True)
    featured["date"] = pd.to_datetime(featured["date"], errors="coerce")
    if featured["date"].isna().any():
        raise ValueError("add_features requires valid dates")
    featured["amount"] = pd.to_numeric(featured["amount"], errors="coerce")
    if featured["amount"].isna().any() or (featured["amount"] <= 0).any():
        raise ValueError("add_features requires positive numeric amounts")

    featured["month"] = featured["date"].dt.to_period("M").astype("string")
    featured["month_start"] = featured["date"].dt.to_period("M").dt.to_timestamp()
    featured["year"] = featured["date"].dt.year.astype(int)
    featured["month_name"] = featured["date"].dt.strftime("%B")
    featured["weekday"] = featured["date"].dt.day_name()
    featured["day_of_week"] = featured["weekday"]
    featured["is_weekend"] = featured["date"].dt.dayofweek >= 5
    featured["day_of_month"] = featured["date"].dt.day.astype(int)
    featured["amount"] = featured["amount"].round(2)
    return featured


def _summary_by_group(df: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Build the same readable metrics for a category-like grouping."""
    if df.empty:
        return pd.DataFrame(
            columns=["category", "total_amount", "transaction_count", "average_amount", "share_pct"]
        ).rename(columns={"category": group_column})

    summary = (
        df.groupby(group_column, as_index=False, dropna=False)
        .agg(
            total_amount=("amount", "sum"),
            transaction_count=("amount", "size"),
            average_amount=("amount", "mean"),
        )
        .sort_values("total_amount", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    total = float(df["amount"].sum())
    summary["share_pct"] = (
        summary["total_amount"].div(total).mul(100).fillna(0) if total else 0.0
    )
    summary["total_amount"] = summary["total_amount"].round(2)
    summary["average_amount"] = summary["average_amount"].round(2)
    summary["share_pct"] = summary["share_pct"].round(2)
    return summary


def _empty_monthly_summary() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["month", "total_amount", "transaction_count", "average_amount", "share_pct"]
    )


def _empty_budget_status() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "category",
            "monthly_budget",
            "period_budget",
            "budget",
            "actual_spend",
            "spent",
            "remaining_budget",
            "remaining",
            "utilization_pct",
            "status",
        ]
    )


def analyze_expenses(df: pd.DataFrame) -> dict[str, Any]:
    """Return summary tables, KPIs, and category budget status.

    Input is cleaned inside this function as a safety net, so callers may pass
    either raw generated rows or an already-cleaned/featured DataFrame.
    """
    _require_dataframe(df, "analyze_expenses")
    cleaned = clean_expenses(df)
    featured = add_features(cleaned)

    category_summary = _summary_by_group(featured, "category")
    payment_summary = _summary_by_group(featured, "payment_method")

    if featured.empty:
        monthly_summary = _empty_monthly_summary()
        weekday_summary = pd.DataFrame(
            {
                "weekday": WEEKDAYS,
                "total_amount": [0.0] * len(WEEKDAYS),
                "transaction_count": [0] * len(WEEKDAYS),
                "average_amount": [0.0] * len(WEEKDAYS),
                "share_pct": [0.0] * len(WEEKDAYS),
            }
        )
        budget_status = _empty_budget_status()
        kpis = {
            "total_spend": 0.0,
            "transaction_count": 0,
            "average_transaction": 0.0,
            "median_transaction": 0.0,
            "largest_expense": 0.0,
            "smallest_expense": 0.0,
            "top_category": None,
            "top_category_spend": 0.0,
            "top_month": None,
            "top_month_spend": 0.0,
            "budget_total": 0.0,
            "budget_used_pct": 0.0,
            "date_start": None,
            "date_end": None,
        }
        return {
            "category_summary": category_summary,
            "monthly_summary": monthly_summary,
            "payment_summary": payment_summary,
            "weekday_summary": weekday_summary,
            "kpis": kpis,
            "budget_status": budget_status,
        }

    monthly_summary = (
        featured.groupby("month", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            transaction_count=("amount", "size"),
            average_amount=("amount", "mean"),
        )
        .sort_values("month", kind="stable")
        .reset_index(drop=True)
    )
    total_spend = float(featured["amount"].sum())
    monthly_summary["share_pct"] = (
        monthly_summary["total_amount"].div(total_spend).mul(100).fillna(0)
    )
    for column in ["total_amount", "average_amount", "share_pct"]:
        monthly_summary[column] = monthly_summary[column].round(2)

    weekday_summary = (
        featured.groupby("weekday", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            transaction_count=("amount", "size"),
            average_amount=("amount", "mean"),
        )
        .set_index("weekday")
        .reindex(WEEKDAYS, fill_value=0)
        .reset_index()
    )
    weekday_summary["share_pct"] = (
        weekday_summary["total_amount"].div(total_spend).mul(100).fillna(0)
    )
    for column in ["total_amount", "average_amount", "share_pct"]:
        weekday_summary[column] = weekday_summary[column].round(2)
    weekday_summary["transaction_count"] = weekday_summary["transaction_count"].astype(int)

    observed_months = max(int(featured["month"].nunique()), 1)
    actual_by_category = featured.groupby("category")["amount"].sum().to_dict()
    categories = list(MONTHLY_BUDGETS)
    extra_categories = sorted(set(featured["category"].dropna()) - set(categories))
    categories.extend(extra_categories)
    budget_rows = []
    for category in categories:
        monthly_budget = float(MONTHLY_BUDGETS.get(category, DEFAULT_MONTHLY_BUDGET))
        period_budget = monthly_budget * observed_months
        actual_spend = float(actual_by_category.get(category, 0.0))
        remaining_budget = period_budget - actual_spend
        utilization_pct = (actual_spend / period_budget * 100) if period_budget else 0.0
        budget_rows.append(
            {
                "category": category,
                "monthly_budget": _round_currency(monthly_budget),
                "period_budget": _round_currency(period_budget),
                "budget": _round_currency(period_budget),
                "actual_spend": _round_currency(actual_spend),
                "spent": _round_currency(actual_spend),
                "remaining_budget": _round_currency(remaining_budget),
                "remaining": _round_currency(remaining_budget),
                "utilization_pct": round(utilization_pct, 2),
                "status": "Over budget" if actual_spend > period_budget else "On track",
            }
        )
    budget_status = (
        pd.DataFrame(budget_rows)
        .sort_values(["utilization_pct", "actual_spend"], ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    budget_total = float(budget_status["period_budget"].sum())

    top_category_row = category_summary.iloc[0]
    top_month_row = monthly_summary.loc[monthly_summary["total_amount"].idxmax()]
    kpis = {
        "total_spend": _round_currency(total_spend),
        "transaction_count": int(len(featured)),
        "average_transaction": _round_currency(featured["amount"].mean()),
        "median_transaction": _round_currency(featured["amount"].median()),
        "largest_expense": _round_currency(featured["amount"].max()),
        "smallest_expense": _round_currency(featured["amount"].min()),
        "top_category": str(top_category_row["category"]),
        "top_category_spend": _round_currency(top_category_row["total_amount"]),
        "top_month": str(top_month_row["month"]),
        "top_month_spend": _round_currency(top_month_row["total_amount"]),
        "budget_total": _round_currency(budget_total),
        "budget_used_pct": round(total_spend / budget_total * 100, 2) if budget_total else 0.0,
        "date_start": featured["date"].min().strftime("%Y-%m-%d"),
        "date_end": featured["date"].max().strftime("%Y-%m-%d"),
    }

    return {
        "category_summary": category_summary,
        "monthly_summary": monthly_summary,
        "payment_summary": payment_summary,
        "weekday_summary": weekday_summary,
        "kpis": kpis,
        "budget_status": budget_status,
    }


def _plot_empty(ax: plt.Axes, message: str = "No data available") -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_axis_off()


def create_visualizations(
    df: pd.DataFrame,
    analysis: dict[str, Any],
    output_dir: str | Path = "outputs",
    image_dir: str | Path = "images",
) -> dict[str, Path]:
    """Create five PNG charts and return their pathlib paths."""
    _require_dataframe(df, "create_visualizations")
    if not isinstance(analysis, dict):
        raise TypeError("create_visualizations expects an analysis dictionary")
    image_path = _path_and_create(image_dir)
    _path_and_create(output_dir)
    sns.set_theme(style="whitegrid")

    paths: dict[str, Path] = {}

    category_summary = analysis.get("category_summary", pd.DataFrame())
    fig, ax = plt.subplots(figsize=(9, 5))
    if isinstance(category_summary, pd.DataFrame) and not category_summary.empty:
        sns.barplot(
            data=category_summary,
            x="total_amount",
            y="category",
            color="#4C78A8",
            ax=ax,
        )
        ax.set_title("Spending by Category")
        ax.set_xlabel("Total amount ($)")
        ax.set_ylabel("")
    else:
        _plot_empty(ax)
    fig.tight_layout()
    paths["category"] = image_path / "spending_by_category.png"
    fig.savefig(paths["category"], dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 8))
    if isinstance(category_summary, pd.DataFrame) and not category_summary.empty:
        ax.pie(
            category_summary["total_amount"],
            labels=category_summary["category"],
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"linewidth": 1, "edgecolor": "white"},
        )
        ax.set_title("Share of Spending by Category")
    else:
        _plot_empty(ax)
    fig.tight_layout()
    paths["category_pie"] = image_path / "spending_by_category_pie.png"
    fig.savefig(paths["category_pie"], dpi=150, bbox_inches="tight")
    plt.close(fig)

    monthly_summary = analysis.get("monthly_summary", pd.DataFrame())
    fig, ax = plt.subplots(figsize=(10, 5))
    if isinstance(monthly_summary, pd.DataFrame) and not monthly_summary.empty:
        sns.lineplot(
            data=monthly_summary,
            x="month",
            y="total_amount",
            marker="o",
            color="#F58518",
            ax=ax,
        )
        ax.set_title("Monthly Spending Trend")
        ax.set_xlabel("Month")
        ax.set_ylabel("Total amount ($)")
        ax.tick_params(axis="x", rotation=45)
    else:
        _plot_empty(ax)
    fig.tight_layout()
    paths["monthly"] = image_path / "monthly_spending.png"
    fig.savefig(paths["monthly"], dpi=150, bbox_inches="tight")
    plt.close(fig)

    payment_summary = analysis.get("payment_summary", pd.DataFrame())
    fig, ax = plt.subplots(figsize=(8, 5))
    if isinstance(payment_summary, pd.DataFrame) and not payment_summary.empty:
        sns.barplot(
            data=payment_summary,
            x="payment_method",
            y="total_amount",
            color="#54A24B",
            ax=ax,
        )
        ax.set_title("Spending by Payment Method")
        ax.set_xlabel("")
        ax.set_ylabel("Total amount ($)")
        ax.tick_params(axis="x", rotation=20)
    else:
        _plot_empty(ax)
    fig.tight_layout()
    paths["payment"] = image_path / "spending_by_payment_method.png"
    fig.savefig(paths["payment"], dpi=150, bbox_inches="tight")
    plt.close(fig)

    weekday_summary = analysis.get("weekday_summary", pd.DataFrame())
    fig, ax = plt.subplots(figsize=(9, 5))
    if isinstance(weekday_summary, pd.DataFrame) and not weekday_summary.empty:
        sns.barplot(
            data=weekday_summary,
            x="weekday",
            y="total_amount",
            color="#B279A2",
            ax=ax,
        )
        ax.set_title("Spending by Day of Week")
        ax.set_xlabel("")
        ax.set_ylabel("Total amount ($)")
        ax.tick_params(axis="x", rotation=25)
    else:
        _plot_empty(ax)
    fig.tight_layout()
    paths["weekday"] = image_path / "spending_by_weekday.png"
    fig.savefig(paths["weekday"], dpi=150, bbox_inches="tight")
    plt.close(fig)

    return paths


def generate_insights(df: pd.DataFrame, analysis: dict[str, Any]) -> list[str]:
    """Turn numeric summaries into short, readable observations."""
    _require_dataframe(df, "generate_insights")
    if not isinstance(analysis, dict):
        raise TypeError("generate_insights expects an analysis dictionary")
    kpis = analysis.get("kpis", {})
    if not kpis or int(kpis.get("transaction_count", 0)) == 0:
        return ["No expense records are available after cleaning, so there are no insights yet."]

    insights = [
        f"Total spending was {_currency(kpis.get('total_spend'))} across "
        f"{int(kpis.get('transaction_count', 0)):,} transactions, averaging "
        f"{_currency(kpis.get('average_transaction'))} per transaction.",
    ]

    top_category = kpis.get("top_category")
    if top_category:
        insights.append(
            f"{top_category} was the largest spending category at "
            f"{_currency(kpis.get('top_category_spend'))}."
        )
    if kpis.get("top_month"):
        insights.append(
            f"The highest-spend month was {kpis['top_month']} at "
            f"{_currency(kpis.get('top_month_spend'))}."
        )

    budget_status = analysis.get("budget_status")
    if isinstance(budget_status, pd.DataFrame) and not budget_status.empty:
        over_budget = budget_status.loc[budget_status["status"].eq("Over budget")]
        if not over_budget.empty:
            category = str(over_budget.iloc[0]["category"])
            utilization = float(over_budget.iloc[0]["utilization_pct"])
            insights.append(
                f"{category} is over its illustrative budget at {utilization:.1f}% used."
            )
        else:
            insights.append("All tracked categories are within their illustrative budgets.")

    weekday_summary = analysis.get("weekday_summary")
    if isinstance(weekday_summary, pd.DataFrame) and not weekday_summary.empty:
        highest_day = weekday_summary.loc[weekday_summary["total_amount"].idxmax()]
        insights.append(
            f"{highest_day['weekday']} had the highest total spending at "
            f"{_currency(highest_day['total_amount'])}."
        )
    return insights


def _json_value(value: Any) -> Any:
    """Convert common pandas/numpy scalars to values accepted by json.dumps."""
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value):
        return None
    return value


def _dataframe_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {str(key): _json_value(value) for key, value in record.items()}
        for record in frame.to_dict(orient="records")
    ]


def save_analysis_outputs(
    df: pd.DataFrame,
    analysis: dict[str, Any],
    insights: list[str],
    output_dir: str | Path = "outputs",
) -> dict[str, Path]:
    """Save cleaned data, summary CSVs, KPIs, and text insights."""
    _require_dataframe(df, "save_analysis_outputs")
    if not isinstance(analysis, dict):
        raise TypeError("save_analysis_outputs expects an analysis dictionary")
    if not isinstance(insights, list) or not all(isinstance(item, str) for item in insights):
        raise TypeError("insights must be a list of strings")
    output_path = _path_and_create(output_dir)

    paths: dict[str, Path] = {}
    paths["expenses"] = output_path / "cleaned_expenses.csv"
    df.to_csv(paths["expenses"], index=False)

    for key in ["category_summary", "monthly_summary", "payment_summary", "weekday_summary", "budget_status"]:
        value = analysis.get(key)
        if not isinstance(value, pd.DataFrame):
            raise ValueError(f"analysis['{key}'] must be a pandas DataFrame")
        paths[key] = output_path / f"{key}.csv"
        value.to_csv(paths[key], index=False)

    kpis = analysis.get("kpis")
    if not isinstance(kpis, dict):
        raise ValueError("analysis['kpis'] must be a dictionary")
    paths["kpis"] = output_path / "kpis.json"
    with paths["kpis"].open("w", encoding="utf-8") as handle:
        json.dump({key: _json_value(value) for key, value in kpis.items()}, handle, indent=2)
        handle.write("\n")

    paths["insights"] = output_path / "insights.txt"
    paths["insights"].write_text("\n".join(insights) + "\n", encoding="utf-8")

    serializable_analysis = {
        key: (_dataframe_records(value) if isinstance(value, pd.DataFrame) else value)
        for key, value in analysis.items()
    }
    paths["analysis"] = output_path / "analysis.json"
    with paths["analysis"].open("w", encoding="utf-8") as handle:
        json.dump(serializable_analysis, handle, default=_json_value, indent=2)
        handle.write("\n")

    return paths
