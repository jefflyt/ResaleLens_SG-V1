---
description: Bootstrap a greenfield project from a PSD (PR0).
---

1. **Gather Context**:
   - Locate the **Product Specification Document (PSD)** at `docs/psd/PSD.md`.
   - If not found, ask the user to provide it or run `/create_psd` first.
   - **Confirm the project type** from the PSD before proceeding.

2. **Run Bootstrap Instructions**:
   - Execute the following instruction text:

    ---
    You are bootstrapping a brand-new repo from a PSD. There is NO existing codebase, NO scripts, NO CI.
    Your output MUST define PR0: Project Bootstrap so the repo becomes runnable and establishes a source of truth for future workflows.

    ## Hard rules
    - Do NOT write feature implementation code.
    - Do NOT output fenced code blocks.
    - Do NOT invent commands after the fact: all commands you define must be consistent and form a runnable toolchain.
    - Select the stack based on the **project type** defined in the PSD.

    ## Python Presets (by Project Type)

    ### Backend API
    - FastAPI + Pydantic + Uvicorn
    - SQLAlchemy + Alembic (if DB needed)
    - uv or pip + venv
    - pytest + pytest-cov
    - Ruff (lint + format)
    - mypy (typecheck)
    - .env (python-dotenv)

    ### Data Dashboard
    - Streamlit or Dash
    - Pandas/Polars + DuckDB
    - uv or pip + venv
    - pytest
    - Ruff

    ### Full-Stack Web (Python)
    - Django (with templates) OR FastAPI + Jinja2 + HTMX
    - SQLAlchemy/Django ORM + migrations
    - uv or pip + venv
    - pytest
    - Ruff + mypy

    ### CLI Tool
    - Typer or Click
    - uv or pip + venv
    - pytest
    - Ruff

    ### Automation/Pipeline
    - Python + APScheduler or Prefect
    - uv or pip + venv
    - pytest
    - Ruff

    ## Output Format (MUST follow)

    # PR0: Project Bootstrap

    ## 0) Project Type
    - [From PSD: Backend API / Dashboard / Web App / CLI / Automation / ML]

    ## 1) Assumptions (max 3)
    - [Assumption 1]
    - [Assumption 2]

    ## 2) PSD Extraction (scaffolding-relevant only)
    - App type:
    - Key pages/flows (names only):
    - Data needs (none/SQLite/Postgres):
    - Auth need (none/basic/OAuth):

    ## 3) Tech Decisions (DECIDED)
    - Stack preset: [from presets above]
    - Package manager: uv / pip+venv
    - Test runner: pytest
    - Lint/format: Ruff
    - Typecheck: mypy (optional)
    - Environment strategy (.env.*): python-dotenv
    - Minimal CI checks: lint + test

    ## 4) Repo Structure (DECIDED)
    - Top-level folders:
    - Where app code lives: `src/`
    - Where tests live: `tests/`
    - Where config lives: root (pyproject.toml, .env)
    - Where DB/migrations live (if any):

    ## 5) PR0 Details
    - **Goal**:
    - **Scope**:
    - **Files to create**:
      - README.md (setup + commands)
      - pyproject.toml (dependencies, scripts, tool config)
      - .github/workflows/ci.yml (or equivalent CI config)
      - src/__init__.py
      - tests/__init__.py
      - docs/technical/context.md (optional, for shared context)
    - **Commands to establish**:
      - install: `uv sync` or `pip install -e .`
      - dev: `uvicorn src.main:app --reload` (or equivalent)
      - test: `pytest`
      - lint: `ruff check .`
      - format: `ruff format .`
      - typecheck: `mypy src/` (optional)
    - **Verification checklist**:
    - **Risks / gotchas**:

    ## 6) Next Step
    - After PR0 is implemented, run `/plan_product` to generate PR1..n.
    ---

3. **Generate Artifact**:
   - Save the bootstrap plan to `docs/plans/PR0_BOOTSTRAP.md`.

4. **Verification**:
// turbo
   - Confirm the file exists: `ls docs/plans/PR0_BOOTSTRAP.md`

5. **Output**:
   - "Bootstrap plan generated at docs/plans/PR0_BOOTSTRAP.md"

---

## Next Workflow
- **Implement PR0**: `/implement_task` (with `docs/plans/PR0_BOOTSTRAP.md`)
- **After PR0 is done**: `/plan_product` to plan PR1..n
