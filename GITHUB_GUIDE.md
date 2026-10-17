# GitHub Guide — Expense Tracker App

This guide turns the finished Expense Tracker App into a clean, reviewable
GitHub repository. Commands assume a terminal is opened in the project folder
and that Git is installed. Replace `YOUR_USERNAME` with the GitHub account
that owns the repository.

## Repository identity

- **Repository name:** `expense-tracker-app`
- **Description:** `A reproducible Python expense analytics pipeline with an optional Streamlit dashboard.`
- **Visibility:** public for a portfolio project, unless the project contains
  private data or coursework that must remain private.
- **Suggested topics:** `python`, `pandas`, `data-analysis`,
  `data-visualization`, `streamlit`, `expense-tracker`, `portfolio-project`,
  `beginner-data-science`

## 1. Pre-flight checks

Run these before creating the first commit:

```bash
python --version
git --version
git status
```

Review the working tree and confirm that no passwords, API keys, private
financial records, `.venv/`, `__pycache__/`, or accidental large exports are
present. Check that README run commands match the actual core module name.

If the project does not yet have a suitable `.gitignore`, create one before
staging files. A minimal Python project should ignore at least:

```text
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ipynb_checkpoints/
.env
.env.*
outputs/
```

If selected demo outputs are intentionally part of the portfolio, add them
explicitly with `git add -f` only after reviewing them.

## 2. Create the local repository

```bash
cd "/path/to/Expense Tracker App"
git init
git branch -M main
git status
```

The requested presentation layer can be staged explicitly:

```bash
git add README.md GITHUB_GUIDE.md INTERVIEW_PREP.md PROJECT_PLAN.md dashboard.py
git diff --cached --stat
git diff --cached --check
git commit -m "docs: add project presentation and dashboard"
```

If the core implementation, tests, and selected sample outputs are ready,
stage them in separate focused commits rather than hiding everything in one
large upload.

## 3. Recommended commit-message plan

Use imperative, specific Conventional Commit-style messages. A student project
can use this sequence:

```text
chore: add project repository scaffolding
feat: add reproducible synthetic expense generation
feat: add expense cleaning and feature engineering
feat: add grouped expense analysis
feat: add category monthly and payment charts
feat: add generated expense insights
feat: add optional Streamlit dashboard
test: cover cleaning analysis and output reconciliation
docs: add project README and learning guide
docs: add interview preparation and project plan
chore: add portfolio screenshots
```

Use the smallest truthful message for each change. Do not use messages such
as `update`, `final`, or `changes` because they do not explain the history.
If the five requested files are all the first deliverable, the single
`docs: add project presentation and dashboard` commit is sufficient.

## 4. Create the GitHub repository and connect it

Create an empty repository on GitHub named `expense-tracker-app`. Do not add a
second README, `.gitignore`, or license from the GitHub form if those files
already exist locally; that avoids an unnecessary initial merge.

Then connect and verify the remote:

```bash
git remote add origin https://github.com/YOUR_USERNAME/expense-tracker-app.git
git remote -v
git push -u origin main
```

For SSH instead:

```bash
git remote add origin git@github.com:YOUR_USERNAME/expense-tracker-app.git
git remote -v
git push -u origin main
```

GitHub may prompt for browser authentication or a personal access method. Do
not put a token directly into a repository URL or commit it to a file.

## 5. Verify the published repository

After the push, open the repository page and check:

```bash
git status
git log --oneline --decorate -10
git branch -vv
git ls-files
```

On GitHub, confirm that:

- the README renders from the repository root;
- the dashboard command is copy-paste friendly;
- the repository description and topics are set;
- screenshots use relative paths and render correctly;
- no secret, private CSV, virtual environment, or generated cache is visible;
- the default branch is `main`;
- the latest commit contains the intended files.

## 6. Updating the repository safely

For a later change:

```bash
git status
git diff
git add path/to/changed_file.py
git diff --cached --check
git commit -m "feat: describe the user-visible change"
git push
```

Before a release-style polish pass:

```bash
git log --oneline --decorate -10
git status
git diff main...HEAD --stat
```

Keep generated outputs deterministic. If an output changes because the seed or
algorithm changed, explain that in the commit body or README rather than
silently replacing screenshots.

## 7. Optional GitHub features

After the first successful push, consider adding:

- a repository About description and the topics listed above;
- a Python `.gitignore` and an open-source license appropriate to the project;
- a `requirements.txt` or `pyproject.toml` with pinned or bounded versions;
- a GitHub Actions workflow for tests and formatting;
- a Discussions or Issues template only if you expect collaboration;
- a short release note with the screenshots and demo command.

These are follow-up polish steps. The core portfolio proof is a reproducible
run, understandable outputs, clean history, and a README that a reviewer can
follow from a fresh clone.
