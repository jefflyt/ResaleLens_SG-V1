# ResaleLens SG

**HDB Resale Fair Value & Block Analytics Platform for Singapore**

ResaleLens SG is a full-stack web application that provides data-driven insights into Singapore's HDB resale market, helping buyers make informed decisions through fair value analysis, block-level analytics, and comprehensive comparisons.

## Features

- **Fair Value Engine**: AI-powered fair value estimates based on historical transactions, location, and amenities
- **Block X-Ray**: Detailed block-level analytics including transaction history, unit mix, and trends
- **Smart Comparisons**: Side-by-side comparison of multiple units or blocks
- **High-Value Zone Detection**: Identify undervalued opportunities in the resale market
- **PDF Reports**: Generate professional PDF reports for easy sharing
- **Lead Management**: Admin panel for managing callback requests

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: Supabase (PostgreSQL) + SQLAlchemy ORM + Alembic migrations
- **Frontend**: Jinja2 templates + HTMX for interactivity
- **Job Scheduler**: APScheduler for automated data ingestion
- **PDF Generation**: WeasyPrint
- **Testing**: pytest + pytest-cov
- **Code Quality**: Ruff (linting & formatting) + mypy (type checking)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- **Supabase account** with a project created ([Sign up free](https://supabase.com))

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ResaleLens_SG-V1
   ```

2. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up Supabase** (REQUIRED):
   - Create a new project at [supabase.com](https://supabase.com)
   - Go to **Settings → Database → Connection String → URI**
   - Copy your connection string (use the **Connection Pooling** option)
   - See [docs/technical/supabase_setup.md](docs/technical/supabase_setup.md) for detailed guide

4. **Install dependencies**:
   ```bash
   uv sync
   ```

5. **Configure environment variables**:
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` and set **required** variables:
   ```bash
   # REQUIRED: Supabase connection string
   DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
   
   # REQUIRED: Data.gov.sg API (already set in .env.example)
   DATA_GOV_SG_RESOURCE_ID=d_8b84c4ee58e3cfc0ece0d773c8ca6abc
   
   # REQUIRED: OneMap API token (get from https://www.onemap.gov.sg/apidocs/)
   ONEMAP_API_TOKEN=your-token-here
   ```

6. **Validate environment**:
   ```bash
   uv run python scripts/validate_env.py
   ```

7. **Run database migrations**:
   ```bash
   uv run alembic upgrade head
   ```

8. **Verify connections**:
   ```bash
   uv run python scripts/test_connections.py
   ```

### Running the Application

**Development server**:
```bash
uv run uvicorn src.resalelens.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

## Development Commands

| Command | Description |
|---------|-------------|
| `uv sync` | Install/update dependencies |
| `uv run uvicorn src.resalelens.main:app --reload` | Start development server with auto-reload |
| `uv run pytest` | Run all tests |
| `uv run pytest --cov=src --cov-report=term-missing` | Run tests with coverage report |
| `uv run ruff check .` | Lint codebase |
| `uv run ruff format .` | Format codebase |
| `cd src && uv run mypy resalelens/` | Run type checker |
| `uv run alembic upgrade head` | Apply database migrations |
| `uv run alembic revision --autogenerate -m "message"` | Generate new migration |
| `uv run python scripts/setup_db.py` | Initialize database (first-time setup) |

## Project Structure

```
ResaleLens_SG-V1/
├── src/resalelens/          # Application code
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # ORM models
│   ├── scheduler.py         # APScheduler setup
│   └── migrations/          # Alembic migrations
├── tests/                   # Test suite
├── templates/               # Jinja2 HTML templates
├── static/                  # Static assets (CSS, JS, images)
├── data/                    # Local data storage (SQLite DB, datasets)
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
│   ├── psd/                 # Product specifications
│   ├── plans/               # Implementation plans
│   └── technical/           # Technical documentation
├── .github/workflows/       # CI configuration
├── pyproject.toml           # Project config & dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

## Architecture

ResaleLens is built as a monolithic FastAPI application with server-side rendering using Jinja2 templates and HTMX for dynamic interactions. This approach provides:

- **Simplicity**: No complex frontend build pipeline
- **Performance**: Server-side rendering with minimal client-side JavaScript
- **SEO-friendly**: Fully rendered HTML pages
- **Developer productivity**: Rapid iteration with auto-reload

### Key Design Decisions

- **FastAPI + Jinja2 + HTMX** over React/Next.js for MVP simplicity
- **SQLite for local development**, **Supabase PostgreSQL for production/MVP validation**
- **APScheduler** for automated data ingestion (HDB transactions, POIs, MRT locations)
- **WeasyPrint** for PDF generation (Python-based, server-side)

> **📌 Database Setup:**  
> - **Local Development**: Uses SQLite (`data/resalelens.db`) - zero configuration needed  
> - **Production/MVP**: Uses Supabase PostgreSQL (Singapore region)
> 
> **Quick Supabase Setup**:
> ```bash
> # 1. Create Supabase project at https://app.supabase.com (Singapore region)
> # 2. Copy connection string and add to .env.local:
> DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
> 
> # 3. Run migrations and seed data:
> uv run alembic upgrade head
> uv run python scripts/seed_data.py
> ```
> 
> **See [Supabase Setup Guide](docs/technical/supabase_setup.md) for detailed instructions.**

## Testing

Run the test suite:
```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Code Quality

**Linting**:
```bash
uv run ruff check .
```

**Formatting**:
```bash
uv run ruff format .
```

**Type checking**:
```bash
cd src && uv run mypy resalelens/
```

## CI/CD

GitHub Actions workflow runs on every push and pull request:
- Linting (Ruff)
- Formatting check (Ruff)
- Type checking (mypy)
- Test suite (pytest)

## AI-Driven Development

This project leverages **Antigravity**, an advanced agentic AI coding assistant, to streamline planning, implementation, and maintenance. We follow a structured workflow to ensure code quality and maintainable documentation.

### Agent Workflows

Use the following workflows to interact with the AI agent:

#### Setup & Planning
- **/create_psd**: Validate and refine a user-provided Product Specification Document (PSD)
- **/plan_product**: Generate high-level architecture and a PR breakdown from a PSD
- **/bootstrap_repo**: Initialize a greenfield project based on a PSD

#### Feature Development
- **/plan_epic**: Break down a large feature (Epic) into manageable, testable PRs
- **/plan_feature**: Plan a specific feature that fits within a single PR
- **/implement_task**: Execute a planned task or PR, generating code and tests

#### Maintenance
- **/plan_refactor**: Plan a code refactoring task that preserves existing behavior

## Contributing

See `docs/technical/context.md` for developer onboarding and architecture details.

## License

[Your License Here]

---

Built with ❤️ for Singapore's HDB community
