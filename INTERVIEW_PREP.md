# Interview Prep — Expense Tracker App

Use this sheet to explain the Expense Tracker App in clear student-level
language. A strong answer starts with the user problem, names the technical
choice, gives evidence, and acknowledges a limitation.

## 1. Give me a quick overview of the project.

**Strong answer:**

> I built an Expense Tracker App that turns transaction records into cleaned
> data, summary tables, visualizations, and short insights. The core pipeline
> is separated into generation, cleaning, feature engineering, analysis,
> visualization, insight generation, and output saving. I also added an
> optional Streamlit dashboard where a user can upload a CSV or generate
> synthetic data, filter by date/category/payment method, and see KPIs and
> charts. I used synthetic data for a reproducible public demo, so I could
> publish the project without exposing financial information.

**Technical explanation:** This is a batch analytics pipeline with a thin
presentation adapter. The core API is deliberately small and the dashboard
should not own the business calculations.

## 2. Why did you choose synthetic data?

**Strong answer:**

> I wanted the repository to be safe to share and easy for another person to
> run. A fixed random seed makes the demo reproducible, and synthetic data lets
> me include realistic categories, amounts, dates, and payment methods without
> publishing private transactions. I would not claim that the synthetic
> patterns represent real consumer behavior; with real data I would need
> consent, redaction, secure storage, and additional domain validation.

**Technical explanation:** Synthetic generation is an input adapter, not a
statistical claim. The limitation is documented and the pipeline can accept a
real CSV with the same canonical schema.

## 3. How do you clean the expense data?

**Strong answer:**

> I standardize column names, parse dates, convert amount text such as `$1,200`
> into numeric values, handle missing categories/payment methods explicitly,
> and remove rows that cannot provide a valid date and amount. I keep the
> cleaning step separate so it can be tested independently and so later
> analysis receives a predictable schema.

**Technical explanation:** Date parsing uses coercion to identify invalid rows;
numeric calculations remain numeric and display formatting is applied only at
the presentation boundary. In a production version I would emit a data-quality
report with counts for every decision.

## 4. Why are feature engineering and the `month` field useful?

**Strong answer:**

> A transaction date is useful for a row, but it is not yet a useful grouping
> key for a monthly trend. I derive fields such as month, weekday, or quarter
> only when they answer a question. The month field lets me aggregate spending
> consistently and compare periods without repeating date logic in every chart.

**Technical explanation:** Derived fields create a shared analytical contract.
They should be deterministic, documented, and added after date validation.

## 5. How do you know your totals are correct?

**Strong answer:**

> I reconcile the total spend against the grouped summaries. The total in the
> cleaned data should equal the sum of the category, month, and payment-method
> summaries, apart from final display rounding. I would also test row counts,
> non-negative amounts, required columns, and a small hand-calculated fixture.

**Technical explanation:** Reconciliation is an invariant across independent
group-bys. It catches dropped rows, duplicated rows, and inconsistent filters
better than checking a single chart by eye.

## 6. Why use a Streamlit dashboard instead of only a notebook?

**Strong answer:**

> A notebook is excellent for exploration, but a dashboard makes the final
> question easier to demonstrate: choose a data source, apply filters, and
> inspect the same metrics without rerunning cells manually. Streamlit gives me
> that interaction with a small amount of code. I still keep the core pipeline
> outside the dashboard so the analysis remains reusable and testable.

**Technical explanation:** Streamlit is the presentation layer. Its rerun model
is acceptable for a small local dataset; a larger or multi-user product would
need caching, a service boundary, persistence, and access controls.

## 7. What happens when a user uploads a bad CSV?

**Strong answer:**

> The dashboard checks for the required fields and shows a readable error when
> the table cannot be interpreted. It parses dates and amounts, drops rows that
> have no valid values for those required measures, and labels missing
> categories or payment methods as `Unknown`. I would improve the next version
> with a row-level validation report so the user can download rejected records
> and reasons.

**Technical explanation:** The UI handles the user-facing failure state while
the core cleaning function should remain the source of truth for validation
rules.

## 8. How did you decide which charts to include?

**Strong answer:**

> I chose charts that answer three different questions: category spend shows
> where money goes, the monthly line shows when spending changes, and the
> payment-method chart shows how transactions are paid. I also include KPIs for
> total, count, average, and top category so a reviewer can scan the result
> before exploring details.

**Technical explanation:** The chart set is intentionally small and tied to
analysis outputs. Each chart uses a stable aggregation and clear units rather
than adding decorative visuals.

## 9. What would you improve for production?

**Strong answer:**

> I would add stronger schema validation, currency and locale handling,
> merchant normalization, budget comparisons, and automated tests around the
> public functions. For multiple users I would add authenticated storage and a
> database rather than treating a CSV as the system of record. I would also add
> CI, logging, and a data-quality report before deploying.

**Technical explanation:** The current project is intentionally local and
single-user. A production design would separate ingestion, processing,
storage, and serving, and would define privacy and retention rules.

## 10. What was the hardest engineering decision?

**Strong answer:**

> The hardest decision was keeping the dashboard useful without coupling it to
> one exact core-module filename or function signature. I treated the seven
> public functions as the contract, used an environment variable for a custom
> module path, normalized common return shapes, and kept a deterministic preview
> fallback. That lets the presentation layer be demonstrated while still
> encouraging a clean core boundary. The trade-off is that a real production
> project should use an explicit typed interface rather than a permissive
> adapter.

**Technical explanation:** The dashboard adapter is a compatibility layer for a
student project. Once the core API is fixed, it can be simplified and made
stricter with explicit types and validation.

## HR-style prompts

### Tell me about a project you are proud of.

Focus on the user problem, the pipeline boundary, and the evidence: “I can
show the generated outputs, reconciliation checks, dashboard filters, and a
five-day build trail.” Avoid describing only libraries.

### What did you learn from this project?

Mention that clean input contracts and reproducible seeds matter as much as
charts. Explain that you learned to separate computation from presentation and
to document limitations rather than overclaiming.

### Tell me about a mistake or limitation.

Use synthetic data as the honest example: it is safe and reproducible but not
representative of all real spending. Then state the improvement—real-data
consent/redaction, validation, currency support, and domain tests.

### How do you prioritize improvements?

Start with correctness and reproducibility, then clarity and usability, then
scale. For this project that means reconciliation tests and schema validation
before adding more charts or a database.

### How do you work with feedback?

Say that you turn feedback into an observable acceptance criterion. For
example, “make the app easier to run” becomes a copy-paste install command, a
clear missing-dependency hint, and a fresh-clone check.

## Technical concepts to review

- pandas `DataFrame`, grouping, joins, missing values, and date parsing;
- the difference between raw, cleaned, featured, and aggregate datasets;
- descriptive statistics versus causal inference and forecasting;
- reproducibility, fixed seeds, deterministic outputs, and reconciliation;
- Streamlit reruns, widgets, empty/error states, and optional dependencies;
- unit tests for transformations versus integration tests for the pipeline;
- Git staging, focused commits, remotes, and keeping secrets out of history;
- CSV limitations, currency precision, time zones, and privacy of financial data.

## A concise closing statement

> This project shows that I can take an ambiguous data question, define a
> schema, build a reproducible pipeline, validate the results, present the
> findings interactively, and explain both the technical choices and the
> limitations. I would keep the current simple architecture for a portfolio
> demo and add persistence, security, and stronger validation only when the
> product requirements justify them.
