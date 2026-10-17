# Project Plan — Expense Tracker App

This plan turns the Expense Tracker App into a small, reviewable, and
portfolio-ready system. It assumes a core module with this public API:

```text
generate_synthetic_expenses
clean_expenses
add_features
analyze_expenses
create_visualizations
generate_insights
save_analysis_outputs
```

The optional `dashboard.py` is a presentation layer. It should call the core
contract rather than recreate analysis rules inside Streamlit widgets.

## 1. Outcome and success definition

A new user should be able to clone the project, install the documented
packages, run the pipeline with a fixed seed, inspect saved artifacts, and
launch an optional dashboard. A reviewer should be able to explain what each
stage does, verify that grouped totals reconcile, and see a meaningful response
to date/category/payment-method filters.

## 2. Capability map

| Capability | Owner | User-visible result |
| --- | --- | --- |
| Generate input | `generate_synthetic_expenses` | Reproducible rows with date, amount, category, and payment method |
| Clean data | `clean_expenses` | Canonical, valid analytical table and documented handling of invalid rows |
| Add features | `add_features` | Time/grouping fields such as `month` |
| Analyze | `analyze_expenses` | Totals and grouped summary tables |
| Visualize | `create_visualizations` | Category bar/pie, monthly, payment-method, and weekday charts |
| Explain | `generate_insights` | Evidence-based narrative bullets |
| Persist | `save_analysis_outputs` | Stable CSV, JSON, text, and PNG artifacts |
| Present | `dashboard.py` | Interactive filters, KPIs, charts, preview, and insights |

## 3. Phase roadmap

### Phase 0 — Scope and contract

**What:** Write the problem statement, input schema, output filename contract,
assumptions, and public function signatures.

**Why:** An explicit contract prevents the project from becoming a set of
unconnected charts and lets the dashboard remain a thin client.

**Output:** README, this plan, schema note, and a small example row.

**Common mistakes:** unclear meaning of one row, mixed currencies, and
undocumented function return shapes.

### Phase 1 — Reproducible synthetic data

**What:** Implement a generator with a seed, realistic categories and payment
methods, date spread, and positive numeric amounts.

**Why:** A safe and deterministic input makes the public demo repeatable.

**Output:** a reproducible generated DataFrame, an optional
`data/raw/expenses.csv`, and a generator smoke check.

**Common mistakes:** unseeded randomness, impossible dates, negative amounts
without a stated refund rule, or a generator that returns no schema.

### Phase 2 — Cleaning and validation

**What:** Normalize names, parse dates and amounts, handle missing dimensions,
validate required fields, and report rejected rows.

**Why:** Every later metric depends on trustworthy input.

**Output:** `outputs/cleaned_expenses.csv` and a data-quality summary.

**Common mistakes:** silently treating invalid amounts as zero, dropping rows
without a count, or formatting currency before doing arithmetic.

### Phase 3 — Feature engineering

**What:** Add `month` and only other fields that answer a planned question,
such as weekday or quarter.

**Why:** Shared derived fields make grouped analysis consistent.

**Output:** a featured DataFrame and, when persisted by the orchestration layer, `outputs/featured_expenses.csv`.

**Common mistakes:** deriving month from an unparsed string, mixing time zones,
or adding features that cannot be explained.

### Phase 4 — Analysis and reconciliation

**What:** Calculate total spend, transaction count, mean, min, max, and grouped
category/month/payment summaries.

**Why:** Aggregates turn rows into decisions and create invariants for tests.

**Output:** `category_summary.csv`, `monthly_summary.csv`,
`payment_summary.csv`, `weekday_summary.csv`, `budget_status.csv`,
`kpis.json`, and `analysis.json` in `outputs/`.

**Common mistakes:** double-counting after joins, sorting dates as text, and
allowing group totals to disagree with the grand total.

### Phase 5 — Visual communication

**What:** Build clearly labeled category bar, monthly trend line, and payment
method charts. Use consistent currency units and titles.

**Why:** A reviewer should see the main pattern quickly and know what each
visual measures.

**Output:** `images/spending_by_category.png`,
`images/monthly_spending.png`, `images/spending_by_payment_method.png`, and
`images/spending_by_weekday.png`.

**Common mistakes:** decorative charts with no question, truncated axes, or
ambiguous labels.

### Phase 6 — Insight generation

**What:** Convert the strongest descriptive patterns into concise bullets with
numbers and context.

**Why:** Good analysis explains what the reader should notice without claiming
causation that the data cannot support.

**Output:** `outputs/insights.txt` and the insight list included in the
analysis result.

**Common mistakes:** generic advice, unsupported causal claims, and insights
that do not change when the selected data changes.

### Phase 7 — Dashboard integration

**What:** Connect `dashboard.py` to the core contract. Support upload or
synthetic data, date/category/payment-method filters, KPI cards, three charts,
a filtered preview, and generated insight bullets.

**Why:** Interactivity makes the analysis easy to demonstrate and inspect.

**Output:** A local Streamlit app launched with
`python -m streamlit run dashboard.py`.

**Common mistakes:** putting all business logic in the UI, no empty/error
state, importing Streamlit at module import time, or using deprecated APIs.

### Phase 8 — Verification and portfolio proof

**What:** Run smoke checks, tests, reconciliation checks, dashboard review,
README walkthrough, and screenshot capture.

**Why:** A portfolio project needs evidence that another person can reproduce
it.

**Output:** Passing checks, screenshots, focused Git commits, and a clear
GitHub repository.

**Common mistakes:** testing only the happy path, committing private data, or
publishing screenshots that do not match the README commands.

## 4. Acceptance criteria

### Core pipeline

- [ ] `generate_synthetic_expenses` accepts a reproducibility control such as a
      seed and produces the documented required columns.
- [ ] The generated sample is non-empty and contains parseable dates,
      positive numeric amounts, categories, and payment methods.
- [ ] `clean_expenses` returns a predictable table and documents invalid-row
      handling.
- [ ] `add_features` creates a documented month/time field from a validated
      date.
- [ ] `analyze_expenses` returns a grand total and grouped summaries for
      category, month, and payment method.
- [ ] Category, monthly, and payment-method totals reconcile with the grand
      total within a documented rounding tolerance.
- [ ] `create_visualizations` creates readable chart artifacts with titles,
      labels, and units.
- [ ] `generate_insights` returns non-empty bullets supported by the computed
      analysis.
- [ ] `save_analysis_outputs` writes `cleaned_expenses.csv`, the summary CSVs,
      `kpis.json`, `insights.txt`, and `analysis.json`, creating its output
      directory when needed.

### Dashboard

- [ ] `dashboard.py` imports without requiring Streamlit to be installed.
- [ ] Running without optional dependencies prints a clear installation hint
      rather than a traceback.
- [ ] The app can generate synthetic data and load a CSV upload.
- [ ] Sidebar controls filter by date, category, and payment method.
- [ ] KPI cards show total spend, transaction count, average transaction, and
      top category for the filtered data.
- [ ] The app shows a category bar chart, monthly trend line chart, and payment
      method chart.
- [ ] A filtered data preview is visible and limited to a reasonable number of
      rows.
- [ ] Generated insight bullets update with the selected data.
- [ ] Empty, invalid-upload, and missing-core-module states are readable.
- [ ] No deprecated Streamlit calls are used.

### Documentation and publishing

- [ ] README includes installation commands for Windows, macOS, and Linux.
- [ ] README includes simple and technical explanations, workflow, architecture,
      output filenames, screenshots checklist, troubleshooting, and synthetic
      data limitations.
- [ ] GitHub guide includes exact commands and a focused commit-message plan.
- [ ] Interview preparation includes ten technical questions with strong
      student-level answers plus HR prompts.
- [ ] A fresh clone can follow the README without relying on local absolute
      paths or private data.

## 5. Verification checklist

Run checks from the project root. Use the exact commands supported by the core
implementation; these examples are intentionally small:

```bash
python -m compileall dashboard.py
python -m pytest
python -m streamlit run dashboard.py
```

For a pipeline run, verify the output directory and reconcile totals:

```bash
python -c "from pathlib import Path; print(sorted(Path('outputs').rglob('*')))"
```

During a manual dashboard review, test these paths:

1. synthetic data with default filters;
2. a CSV upload with valid rows;
3. an invalid or missing required column;
4. a date range with no matching rows;
5. one category and one payment method selected;
6. all categories or payment methods cleared and then restored;
7. a missing core module with the deterministic preview fallback.

Do not mark a criterion complete because a file exists. Mark it complete only
after the user-visible behavior or artifact has been checked.

## 6. Definition of done

The project is ready for a first GitHub release when the core output contract
is stable, reconciliation checks pass, the dashboard meets its acceptance
criteria, the README works from a fresh environment, screenshots contain no
private data, and the Git history tells the build story in focused commits.
