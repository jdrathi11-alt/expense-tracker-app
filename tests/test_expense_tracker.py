"""Focused tests for the beginner-friendly expense tracker pipeline."""

import pandas as pd

from src.expense_tracker import (
    add_features,
    analyze_expenses,
    clean_expenses,
    create_visualizations,
    generate_insights,
    generate_synthetic_expenses,
    save_analysis_outputs,
)


def test_generate_synthetic_expenses_has_expected_shape_and_columns():
    expenses = generate_synthetic_expenses(n_rows=25, seed=7)

    assert len(expenses) == 25
    assert {
        "expense_id",
        "date",
        "category",
        "description",
        "amount",
        "payment_method",
        "merchant",
    }.issubset(expenses.columns)
    assert pd.api.types.is_datetime64_any_dtype(expenses["date"])
    assert pd.api.types.is_numeric_dtype(expenses["amount"])
    assert expenses["amount"].round(2).equals(expenses["amount"])


def test_clean_expenses_removes_invalid_rows_and_duplicates():
    raw = pd.DataFrame(
        {
            "expense_id": [1, 1, 2, 3, 4],
            "date": [
                "2025-01-01",
                "2025-01-01",
                "not-a-date",
                "2025-01-03",
                "2025-01-04",
            ],
            "category": ["Food", "Food", "Housing", "", "Travel"],
            "amount": [12.50, 12.50, 50.00, 20.00, -5.00],
            "payment_method": ["Card", "Card", "Cash", "Card", "Card"],
        }
    )

    cleaned = clean_expenses(raw)

    assert len(cleaned) == 1
    assert cleaned.iloc[0]["expense_id"] == 1
    assert cleaned.iloc[0]["amount"] == 12.50
    assert cleaned["expense_id"].is_unique


def test_clean_expenses_preserves_distinct_transactions_with_same_amount():
    raw = pd.DataFrame(
        {
            "expense_id": ["EXP-001", "EXP-002"],
            "date": ["2025-01-01", "2025-01-01"],
            "category": ["Food", "Food"],
            "description": ["Coffee", "Lunch"],
            "amount": [12.50, 12.50],
            "payment_method": ["Card", "Card"],
            "merchant": ["Cafe", "Cafe"],
        }
    )

    cleaned = clean_expenses(raw)

    assert len(cleaned) == 2
    assert set(cleaned["description"]) == {"Coffee", "Lunch"}


def test_analysis_totals_and_kpis_match_cleaned_expenses():
    raw = generate_synthetic_expenses(n_rows=40, seed=12, include_quality_issues=False)
    featured = add_features(clean_expenses(raw))

    analysis = analyze_expenses(featured)

    expected_total = round(float(featured["amount"].sum()), 2)
    assert analysis["kpis"]["total_spend"] == expected_total
    assert analysis["kpis"]["transaction_count"] == len(featured)
    assert round(
        float(analysis["category_summary"]["total_amount"].sum()), 2
    ) == expected_total
    assert round(
        float(analysis["monthly_summary"]["total_amount"].sum()), 2
    ) == expected_total
    assert set(
        [
            "category_summary",
            "monthly_summary",
            "payment_summary",
            "weekday_summary",
            "kpis",
            "budget_status",
        ]
    ).issubset(analysis)


def test_generate_insights_returns_useful_text_for_nonempty_data():
    expenses = add_features(
        clean_expenses(
            generate_synthetic_expenses(
                n_rows=30, seed=3, include_quality_issues=False
            )
        )
    )
    analysis = analyze_expenses(expenses)

    insights = generate_insights(expenses, analysis)

    assert insights
    assert all(isinstance(insight, str) and insight.strip() for insight in insights)
    assert any("Total spending" in insight for insight in insights)
    top_category = analysis["category_summary"].iloc[0]["category"]
    assert any(str(top_category) in insight for insight in insights)

def test_visualizations_and_analysis_outputs_are_written(tmp_path):
    cleaned = clean_expenses(
        generate_synthetic_expenses(n_rows=30, seed=21, include_quality_issues=False)
    )
    featured = add_features(cleaned)
    analysis = analyze_expenses(featured)
    insights = generate_insights(featured, analysis)

    image_paths = create_visualizations(
        featured,
        analysis,
        output_dir=tmp_path / "outputs",
        image_dir=tmp_path / "images",
    )
    output_paths = save_analysis_outputs(
        cleaned, analysis, insights, output_dir=tmp_path / "outputs"
    )

    assert len(image_paths) == 5
    assert all(path.exists() for path in image_paths.values())
    assert {"expenses", "category_summary", "monthly_summary", "payment_summary",
            "weekday_summary", "budget_status", "kpis", "insights", "analysis"} == set(output_paths)
    assert all(path.exists() for path in output_paths.values())

