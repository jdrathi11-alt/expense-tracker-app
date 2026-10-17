"""Optional Streamlit dashboard for the Expense Tracker App.

The dashboard is a presentation layer. It looks for a core module exposing
the public functions documented in README.md and uses those functions when
they are available. It also includes a deterministic fallback generator so
the UI can be previewed before the core module is connected.

Run from the project directory with:

    python -m streamlit run dashboard.py

Streamlit is imported only when ``main`` is executed, so importing this file
is safe when the optional dashboard dependency is not installed.
"""

from __future__ import annotations

import importlib
import inspect
import os
import random
import re
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from typing import Any

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - minimal installations only
    pd = None  # type: ignore[assignment]


CORE_MODULE_ENV = "EXPENSE_TRACKER_MODULE"
DEFAULT_CORE_MODULES = (
    "src.expense_tracker",
    "expense_tracker",
    "expense_tracker_core",
    "core",
)
DATA_PARAMETER_NAMES = {
    "data", "df", "expenses", "expense_data", "expense_df", "raw_data",
    "transactions", "cleaned_expenses", "featured_expenses", "analysis",
    "analysis_results", "results",
}
RECORD_PARAMETER_NAMES = {
    "n", "n_rows", "num_rows", "num_records", "n_records", "records",
    "size", "count", "num_expenses",
}


def _require_pandas() -> Any:
    if pd is None:
        raise RuntimeError(
            "pandas is required for the Expense Tracker dashboard. "
            "Install it with: python -m pip install pandas"
        )
    return pd


def _public_function_names() -> tuple[str, ...]:
    return (
        "generate_synthetic_expenses", "clean_expenses", "add_features",
        "analyze_expenses", "create_visualizations", "generate_insights",
        "save_analysis_outputs",
    )


def _load_core_module() -> tuple[Any | None, str | None]:
    """Load a likely core module, or the module named by an environment variable."""
    configured_name = os.getenv(CORE_MODULE_ENV, "").strip()
    candidates = ([configured_name] if configured_name else []) + list(DEFAULT_CORE_MODULES)
    seen: set[str] = set()
    for module_name in candidates:
        if not module_name or module_name in seen:
            continue
        seen.add(module_name)
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        if any(callable(getattr(module, name, None)) for name in _public_function_names()):
            return module, module_name
    return None, None


def _invoke_generate(function: Any, records: int) -> Any:
    """Call a generator while tolerating common record/seed parameter names."""
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return function()
    positional_only: list[Any] = []
    keyword_arguments: dict[str, Any] = {}
    for parameter in signature.parameters.values():
        name = parameter.name.lower()
        if name in RECORD_PARAMETER_NAMES:
            if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
                positional_only.append(records)
            elif parameter.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ):
                keyword_arguments[parameter.name] = records
        elif name == "seed" and parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            keyword_arguments[parameter.name] = 42
        elif name == "include_quality_issues" and parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            # The interactive preview should not intentionally inject bad rows;
            # the uploaded-CSV path still exercises cleaning and validation.
            keyword_arguments[parameter.name] = False
    return function(*positional_only, **keyword_arguments)


def _invoke_with_data(function: Any, data: Any) -> Any:
    """Call a one-input core function using its named data argument or first arg."""
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return function(data)
    parameters = list(signature.parameters.values())
    for parameter in parameters:
        if parameter.name.lower() in DATA_PARAMETER_NAMES:
            if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
                return function(data)
            return function(**{parameter.name: data})
    positional = [
        parameter for parameter in parameters
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    if positional or any(p.kind is inspect.Parameter.VAR_POSITIONAL for p in parameters):
        return function(data)
    if not any(
        p.default is inspect.Parameter.empty
        and p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
        for p in parameters
    ):
        return function()
    return function(data)


def _invoke_insights(function: Any, frame: Any, analysis: Any | None) -> Any:
    """Support both ``generate_insights(data)`` and ``(data, analysis)`` APIs."""
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return function(frame, analysis) if analysis is not None else function(frame)
    parameters = list(signature.parameters.values())
    if len(parameters) < 2 or analysis is None:
        return _invoke_with_data(function, frame)
    values: list[Any] = []
    for parameter in parameters:
        name = parameter.name.lower()
        if name in {"analysis", "analysis_results", "results", "summary"}:
            values.append(analysis)
        elif name in DATA_PARAMETER_NAMES or not values:
            values.append(frame)
        elif parameter.default is inspect.Parameter.empty:
            values.append(analysis)
    if len(values) >= 2:
        try:
            return function(*values[:2])
        except TypeError:
            return function(frame, analysis)
    return _invoke_with_data(function, frame)


def _safe_call(function: Any, *args: Any, **kwargs: Any) -> tuple[Any | None, str | None]:
    try:
        return function(*args, **kwargs), None
    except Exception as error:  # depends on the user's core implementation
        return None, f"{type(error).__name__}: {error}"


def _extract_dataframe(value: Any) -> Any | None:
    """Find a DataFrame in common pipeline return shapes."""
    pandas = _require_pandas()
    if isinstance(value, pandas.DataFrame):
        return value.copy()
    if hasattr(value, "to_pandas") and callable(value.to_pandas):
        try:
            converted = value.to_pandas()
        except Exception:
            converted = None
        if isinstance(converted, pandas.DataFrame):
            return converted.copy()
    if isinstance(value, Mapping):
        for key in (
            "data", "df", "expenses", "cleaned_expenses", "featured_expenses",
            "transactions", "result",
        ):
            if key in value:
                extracted = _extract_dataframe(value[key])
                if extracted is not None:
                    return extracted
        for item in value.values():
            extracted = _extract_dataframe(item)
            if extracted is not None:
                return extracted
    if isinstance(value, (list, tuple)):
        if value and all(isinstance(item, Mapping) for item in value):
            return pandas.DataFrame(value)
        for item in value:
            extracted = _extract_dataframe(item)
            if extracted is not None:
                return extracted
    return None


def _fallback_synthetic_expenses(records: int = 300) -> Any:
    """Create deterministic preview data when no core generator is available."""
    pandas = _require_pandas()
    generator = random.Random(42)
    categories = ["Food", "Transport", "Housing", "Shopping", "Health", "Entertainment"]
    payment_methods = ["Card", "Cash", "Bank transfer", "Digital wallet"]
    today = datetime.now().date()
    rows = []
    for index in range(max(1, records)):
        rows.append({
            "date": today - timedelta(days=generator.randrange(0, 180)),
            "category": generator.choice(categories),
            "payment_method": generator.choice(payment_methods),
            "amount": round(generator.uniform(4.50, 180.00), 2),
            "description": f"Synthetic expense {index + 1}",
        })
    return pandas.DataFrame(rows)


def _column_key(name: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def _standardize_columns(data: Any) -> Any:
    """Return the minimum canonical schema needed by the dashboard."""
    pandas = _require_pandas()
    frame = _extract_dataframe(data)
    if frame is None:
        raise ValueError("The core pipeline did not return a tabular expense dataset.")
    frame = frame.copy()
    aliases = {
        "date": {"date", "transaction_date", "expense_date", "spent_on", "timestamp", "datetime"},
        "amount": {"amount", "expense", "cost", "value", "spend", "total"},
        "category": {"category", "expense_category", "type", "group"},
        "payment_method": {"payment_method", "payment_type", "method", "paid_by", "payment"},
    }
    rename_map: dict[Any, str] = {}
    available = {_column_key(column): column for column in frame.columns}
    for canonical_name, possible_names in aliases.items():
        if canonical_name in frame.columns:
            continue
        matched = next((available[key] for key in possible_names if key in available), None)
        if matched is not None:
            rename_map[matched] = canonical_name
    frame = frame.rename(columns=rename_map)
    required = {"date", "amount", "category", "payment_method"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(
            "CSV data must include date, amount, category, and payment_method "
            f"columns. Missing: {', '.join(missing)}."
        )
    frame["date"] = pandas.to_datetime(frame["date"], errors="coerce", utc=True).dt.tz_localize(None)
    amount_text = frame["amount"].astype("string").str.replace(r"[$€,]", "", regex=True)
    frame["amount"] = pandas.to_numeric(amount_text, errors="coerce")
    for column in ("category", "payment_method"):
        frame[column] = frame[column].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    frame = frame.dropna(subset=["date", "amount"]).copy()
    frame = frame.loc[frame["amount"] > 0].copy()
    if frame.empty:
        raise ValueError("No valid positive-spend rows remain after parsing dates and amounts.")
    frame["month"] = frame["date"].dt.to_period("M").astype(str)
    return frame.sort_values("date").reset_index(drop=True)


def _prepare_data(
    core_module: Any | None,
    use_synthetic: bool,
    uploaded_data: Any | None,
    records: int,
) -> tuple[Any, list[str]]:
    notes: list[str] = []
    current = uploaded_data
    if use_synthetic:
        generated = None
        generator = getattr(core_module, "generate_synthetic_expenses", None) if core_module else None
        if callable(generator):
            result, error = _safe_call(_invoke_generate, generator, records)
            if error:
                notes.append(f"Core synthetic generator failed; using preview data ({error}).")
            else:
                generated = _extract_dataframe(result)
        if generated is None:
            generated = _fallback_synthetic_expenses(records)
            if core_module is None:
                notes.append("Core module not found; using the dashboard's deterministic preview generator.")
        current = generated
    if current is None:
        raise ValueError("Choose a data source or upload a CSV file to continue.")
    for function_name in ("clean_expenses", "add_features"):
        function = getattr(core_module, function_name, None) if core_module else None
        if not callable(function):
            continue
        result, error = _safe_call(_invoke_with_data, function, current)
        if error:
            notes.append(f"Core {function_name} was skipped ({error}).")
            continue
        extracted = _extract_dataframe(result)
        if extracted is not None:
            current = extracted
    return _standardize_columns(current), notes


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _normalise_insights(value: Any) -> list[str]:
    """Convert common insight return shapes into short display bullets."""
    if value is None:
        return []
    if isinstance(value, str):
        result = []
        for line in value.splitlines() or [value]:
            line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
            if line:
                result.append(line)
        return result
    if isinstance(value, Mapping):
        for key in ("insights", "bullets", "recommendations", "messages"):
            if key in value:
                result = _normalise_insights(value[key])
                if result:
                    return result
        return [f"{key.replace('_', ' ').capitalize()}: {item}" for key, item in value.items()]
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            result.extend(_normalise_insights(item))
        return result
    return [str(value)]


def _fallback_insights(frame: Any) -> list[str]:
    if frame.empty:
        return ["No transactions match the current filters."]
    total = float(frame["amount"].sum())
    category_totals = frame.groupby("category")["amount"].sum().sort_values(ascending=False)
    payment_totals = frame.groupby("payment_method")["amount"].sum().sort_values(ascending=False)
    monthly_totals = frame.groupby("month")["amount"].sum().sort_values(ascending=False)
    largest_row = frame.loc[frame["amount"].idxmax()]
    share = float(category_totals.iloc[0] / total) if total else 0.0
    return [
        (
            f"{category_totals.index[0]} is the highest-spend category at "
            f"{_format_money(float(category_totals.iloc[0]))} "
            f"({share:.1%} of filtered spend)."
        ),
        f"{payment_totals.index[0]} accounts for {_format_money(float(payment_totals.iloc[0]))} of filtered spend.",
        f"{monthly_totals.index[0]} is the highest-spend month with {_format_money(float(monthly_totals.iloc[0]))}.",
        f"The largest single transaction is {_format_money(float(largest_row['amount']))} in {largest_row['category']}.",
    ]


def _insights_from_core(core_module: Any | None, frame: Any, analysis: Any | None) -> list[str]:
    function = getattr(core_module, "generate_insights", None) if core_module else None
    if not callable(function):
        return []
    candidates = [analysis, frame] if analysis is not None else [frame]
    for candidate in candidates:
        result, _ = _safe_call(_invoke_insights, function, frame, candidate if candidate is not frame else analysis)
        bullets = _normalise_insights(result)
        if bullets:
            return bullets
    return []


def _date_range(value: Any, fallback_start: date, fallback_end: date) -> tuple[date, date]:
    if isinstance(value, (tuple, list)) and len(value) == 2:
        start, end = value
    else:
        start = end = value
    if not isinstance(start, date) or not isinstance(end, date):
        return fallback_start, fallback_end
    return min(start, end), max(start, end)


def _render_dashboard(st: Any) -> None:
    """Render the interactive dashboard using current Streamlit APIs."""
    pandas = _require_pandas()
    st.set_page_config(page_title="Expense Tracker Dashboard", page_icon="💸", layout="wide")
    st.title("Expense Tracker App")
    st.caption("Explore cleaned expense data, trends, and generated insights.")
    core_module, core_name = _load_core_module()
    with st.sidebar:
        st.header("Data and filters")
        source_mode = st.radio("Data source", ("Generate synthetic data", "Upload CSV"))
        records = st.slider("Synthetic rows", min_value=50, max_value=2_000, value=300, step=50)
        uploaded_file = st.file_uploader("Expense CSV", type=["csv"])
        if core_name:
            st.caption(f"Core module: `{core_name}`")
        else:
            st.caption("Core module not found; presentation fallback is active.")
    uploaded_data = None
    if source_mode == "Upload CSV":
        if uploaded_file is None:
            st.info("Upload a CSV in the sidebar, or switch the data source to synthetic data.")
            return
        try:
            uploaded_data = pandas.read_csv(uploaded_file)
        except Exception as error:
            st.error(f"Could not read the uploaded CSV: {error}")
            return
    try:
        frame, pipeline_notes = _prepare_data(
            core_module=core_module,
            use_synthetic=source_mode == "Generate synthetic data",
            uploaded_data=uploaded_data,
            records=records,
        )
    except (RuntimeError, ValueError) as error:
        st.error(str(error))
        return
    for note in pipeline_notes:
        st.sidebar.info(note)
    minimum_date = frame["date"].min().date()
    maximum_date = frame["date"].max().date()
    with st.sidebar:
        selected_range = st.date_input(
            "Date range", value=(minimum_date, maximum_date),
            min_value=minimum_date, max_value=maximum_date,
        )
        category_options = sorted(frame["category"].unique().tolist())
        selected_categories = st.multiselect("Category", category_options, default=category_options)
        payment_options = sorted(frame["payment_method"].unique().tolist())
        selected_payment_methods = st.multiselect(
            "Payment method", payment_options, default=payment_options
        )
    start_date, end_date = _date_range(selected_range, minimum_date, maximum_date)
    filtered = frame.loc[
        frame["date"].dt.date.between(start_date, end_date)
        & frame["category"].isin(selected_categories)
        & frame["payment_method"].isin(selected_payment_methods)
    ].copy()
    total_spend = float(filtered["amount"].sum())
    transaction_count = int(len(filtered))
    average_transaction = total_spend / transaction_count if transaction_count else 0.0
    category_totals = filtered.groupby("category")["amount"].sum().sort_values(ascending=False)
    top_category = str(category_totals.index[0]) if not category_totals.empty else "—"
    st.subheader("Key metrics")
    metric_one, metric_two, metric_three, metric_four = st.columns(4)
    metric_one.metric("Total spend", _format_money(total_spend))
    metric_two.metric("Transactions", f"{transaction_count:,}")
    metric_three.metric("Average transaction", _format_money(average_transaction))
    metric_four.metric("Top category", top_category)
    st.caption(f"Showing {transaction_count:,} of {len(frame):,} transactions after filters.")
    if filtered.empty:
        st.warning("No transactions match these filters. Adjust the sidebar selections to see charts.")
    else:
        st.subheader("Spending overview")
        category_chart, payment_chart = st.columns(2)
        with category_chart:
            st.write("Category spend")
            st.bar_chart(category_totals.rename("spend"))
        with payment_chart:
            st.write("Payment method spend")
            payment_totals = filtered.groupby("payment_method")["amount"].sum().sort_values(ascending=False)
            st.bar_chart(payment_totals.rename("spend"))
        st.write("Monthly trend")
        monthly_totals = filtered.groupby("month")["amount"].sum().sort_index()
        st.line_chart(monthly_totals.rename("spend"))
    st.subheader("Filtered data preview")
    preview_columns = [
        column for column in (
            "date", "amount", "category", "payment_method", "description", "month"
        ) if column in filtered.columns
    ]
    preview = filtered.loc[:, preview_columns].head(100).copy()
    if "date" in preview.columns:
        preview["date"] = preview["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(preview, hide_index=True)
    analysis = None
    analyze_function = getattr(core_module, "analyze_expenses", None) if core_module else None
    if callable(analyze_function):
        analysis, _ = _safe_call(_invoke_with_data, analyze_function, filtered)
    insights = _insights_from_core(core_module, filtered, analysis) or _fallback_insights(filtered)
    st.subheader("Generated insights")
    st.caption("Insights update when the data source or sidebar filters change.")
    for insight in insights:
        st.write(f"• {insight}")


def main() -> None:
    """Launch the dashboard or print a friendly optional-dependency hint."""
    if pd is None:
        print(
            "The optional Expense Tracker dashboard needs pandas and Streamlit. "
            "Install them with: python -m pip install pandas streamlit"
        )
        return
    try:
        import streamlit as st
    except ModuleNotFoundError as error:
        if error.name == "streamlit" or error.name.startswith("streamlit."):
            print(
                "Streamlit is optional and is not installed. Install the dashboard "
                "dependencies with: python -m pip install streamlit pandas"
            )
            return
        raise
    _render_dashboard(st)


if __name__ == "__main__":
    main()
