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
   cp .env.example .env
   ```
   
   Edit `.env` and set the following **required** variables:

   **a) Supabase Database (REQUIRED)**
   ```bash
   DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```
   
   > **🗄️ Supabase Setup:**  
   > 1. Create free account at [supabase.com](https://supabase.com)
   > 2. Create new project (choose Singapore region)
   > 3. Go to **Settings → Database → Connection String**
   > 4. Select **Connection Pooling** tab
   > 5. Copy the URI and replace `[YOUR-PASSWORD]` with your database password
   > 6. Paste into `.env` as `DATABASE_URL`

   **b) Data.gov.sg API (REQUIRED)**
   ```bash
   # HDB Resale Transactions
   DATA_GOV_SG_TRANSACTION_ID=d_8b84c4ee58e3cfc0ece0d773c8ca6abc
   
   # HDB Property Information
   DATA_GOV_SG_PROPERTY_INFO_ID=d_17f5382f26140b1fdae0ba2ef6239d2f
   ```
   
   > **📊 Data.gov.sg:**  
   > - No registration needed!
   > - Both resource IDs are already set in `.env.example`
   > - Just copy them to your `.env` file
   > - **Transactions**: Historical HDB resale prices
   > - **Property Info**: Block details, unit mix, facilities

   **c) OneMap API (REQUIRED)**
   ```bash
   ONEMAP_EMAIL=your-onemap-email@example.com
   ONEMAP_PASSWORD=your-onemap-password
   ```
   
   > **📍 OneMap Registration:**  
   > 1. Register at [OneMap API](https://www.onemap.gov.sg/apidocs/register)
   > 2. Create a free account with your email
   > 3. Verify your email address
   > 4. Use your registered email and password in `.env`

6. **Run database migrations**:
   ```bash
   uv run alembic upgrade head
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
| `uv run python scripts/check_ingestion_status.py` | Check ingestion run status |
| `uv run python scripts/test_weekly_ingestion.py` | Test complete weekly ingestion |

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

### Architecture

- **Server-side rendering** with Jinja2 templates for fast, SEO-friendly pages
- **HTMX** for dynamic interactions without complex JavaScript
- **PostgreSQL** (Supabase) for reliable, scalable data storage
- **Automated data updates** from official Singapore government sources

### Data Sources

ResaleLens uses official Singapore government data sources:

- **[HDB Resale Transactions](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view)** - Historical resale flat prices (data.gov.sg)
- **[HDB Property Information](https://data.gov.sg/datasets/d_17f5382f26140b1fdae0ba2ef6239d2f/view)** - Block details, unit mix, facilities (data.gov.sg)
- **[OneMap API](https://www.onemap.gov.sg/apidocs/)** - Geolocation and Points of Interest

All data is automatically refreshed **weekly** to ensure accuracy.

**Update Schedule:** Every Sunday at 03:00 SGT

---

## For Developers

> **📌 Database:**  
> - Uses Supabase PostgreSQL (Singapore region)
> 
> **Quick Supabase Setup**:
> ```bash
> # 1. Create Supabase project at https://app.supabase.com (Singapore region)
> # 2. Copy connection string and add to .env.local:
> DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
> 
> # 3. Run migrations:
> uv run alembic upgrade head
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

## Contributing

See `docs/technical/context.md` for developer onboarding and architecture details.

For AI-assisted development workflows, see `.agent/workflows/README.md`.

## License

[Your License Here]

---

Built with ❤️ for Singapore's HDB community
