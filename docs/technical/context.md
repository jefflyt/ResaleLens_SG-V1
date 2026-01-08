# ResaleLens SG - Technical Context

## Project Overview

**ResaleLens SG** is a full-stack web application designed to provide data-driven insights into Singapore's HDB resale market. The platform helps buyers make informed purchasing decisions through:

- Fair value analysis based on historical transaction data
- Block-level analytics and transaction histories
- Comparative analysis tools for multiple units/blocks
- High-value zone detection for identifying undervalued properties
- Professional PDF report generation
- Lead management system for agent callback requests

## Architecture

### Technology Stack

**Backend:**
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.11+**: Latest stable Python with type hints
- **SQLAlchemy 2.0**: SQL toolkit and ORM for database interactions
- **Alembic**: Database migration management
- **APScheduler**: Job scheduling for automated data ingestion

**Frontend:**
- **Jinja2**: Server-side templating engine
- **HTMX**: Dynamic interactions without heavy JavaScript frameworks
- **Vanilla CSS**: Custom styling without dependencies

**Data & Storage:**
- **SQLite**: Local development database
- **PostgreSQL**: Production database (future migration)
- **WeasyPrint**: PDF generation from HTML/CSS

**Development Tools:**
- **uv**: Fast Python package manager
- **pytest**: Testing framework
- **Ruff**: Fast Python linter and formatter
- **mypy**: Static type checker
- **GitHub Actions**: CI/CD pipeline

### Architecture Decisions

#### 1. **FastAPI + Jinja2 + HTMX vs React/Next.js**

**Decision**: Use server-side rendering with FastAPI + Jinja2 + HTMX

**Rationale**:
- **Simplicity**: No complex frontend build pipeline or state management
- **Performance**: Server-side rendering provides fast initial page loads
- **SEO-friendly**: Fully rendered HTML pages without client-side hydration
- **Developer productivity**: Single codebase, rapid iteration with hotreload
- **Resource efficiency**: Less client-side JavaScript = better performance on low-end devices

**Trade-offs**:
- Less suitable for highly interactive SPAs
- Page navigations require full page reloads (mitigated by HTMX for dynamic sections)
- Frontend state management is simpler but less sophisticated

#### 2. **SQLite for Development, PostgreSQL for Production**

**Decision**: Use SQLite during development; migrate to PostgreSQL for production

**Rationale**:
- **Development speed**: SQLite requires no external database server setup
- **Production reliability**: PostgreSQL offers better concurrency, scalability, and features
- **SQLAlchemy abstraction**: ORM allows seamless database switching

**Migration path**:
- All database interactions use SQLAlchemy ORM
- Alembic migrations ensure schema consistency
- Connection string swap via environment variables

#### 3. **APScheduler for Data Ingestion**

**Decision**: Use APScheduler for automated data refresh

**Rationale**:
- **Embedded solution**: No external job queue (Redis, Celery) required for MVP
- **Simplicity**: Python-native, easy to configure and debug
- **Sufficient for MVP**: Handles hourly/daily data ingestion tasks

**Future considerations**:
- For production scale, may migrate to Celery + Redis for distributed task processing

#### 4. **WeasyPrint for PDF Generation**

**Decision**: Use WeasyPrint (Python-based) instead of JavaScript solutions

**Rationale**:
- **Server-side rendering**: Generates PDFs from existing Jinja2 templates
- **Consistency**: Same template engine for web and PDF output
- **No browser dependency**: No need for Puppeteer/Playwright infrastructure

## Database Schema

### Initial Models

**User** - Admin authentication
- `id`: Primary key
- `email`: Unique email address
- `hashed_password`: Bcrypt-hashed password
- `created_at`: Account creation timestamp

**LeadRequest** - Callback requests from buyers
- `id`: Primary key
- `name`: User's name
- `email`: Contact email
- `phone`: Contact phone number (optional)
- `message`: User's inquiry message
- `created_at`: Request timestamp

**Future models** (to be added in subsequent PRs):
- `Transaction`: HDB resale transaction records
- `Block`: Block-level metadata (location, amenities, etc.)
- `Unit`: Individual unit details
- `POI`: Points of interest (MRT, schools, malls, etc.)

## Directory Structure

```
ResaleLens_SG-V1/
├── src/resalelens/          # Main application package
│   ├── __init__.py          # Package marker
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # ORM models
│   ├── scheduler.py         # APScheduler setup
│   └── migrations/          # Alembic migrations
│       ├── env.py           # Migration environment
│       ├── script.py.mako   # Migration template
│       └── versions/        # Migration files
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   └── test_main.py         # Route tests
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JS, images
├── data/                    # SQLite DB, datasets
├── scripts/                 # Setup/utility scripts
├── docs/                    # Documentation
│   ├── psd/                 # Product specs
│   ├── plans/               # Implementation plans
│   └── technical/           # This file
└── .github/workflows/       # CI configuration
```

## Development Workflow

### Initial Setup

1. Clone repository
2. Install `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Install dependencies: `uv sync`
4. Copy `.env.example` to `.env.local` and configure (`.env.local` is git-ignored for secrets)
5. Initialize database: `uv run python scripts/setup_db.py`
6. Run migrations: `uv run alembic upgrade head`

### Daily Development

1. Start dev server: `uv run uvicorn src.resalelens.main:app --reload`
2. Make code changes (auto-reload on save)
3. Run tests: `uv run pytest`
4. Check linting: `uv run ruff check .`
5. Format code: `uv run ruff format .`

### Adding New Features

1. Create feature branch: `git checkout -b feature/feature-name`
2. Implement feature with tests
3. Run full test suite and linting
4. Create migration if schema changed: `uv run alembic revision --autogenerate -m "description"`
5. Commit and push
6. CI runs automatically on push

## Testing Strategy

**Unit Tests**: Test individual functions and methods
**Integration Tests**: Test API endpoints with test database
**E2E Tests**: (Future) Browser-based testing with Playwright

All tests use in-memory SQLite database to ensure isolation and speed.

## CI/CD Pipeline

**GitHub Actions Workflow**:
- Trigger: Push to `main`, pull requests
- Steps:
  1. Set up Python 3.11
  2. Install uv
  3. Install dependencies (`uv sync`)
  4. Run linting (`ruff check .`)
  5. Run format check (`ruff format --check .`)
  6. Run type checking (`mypy src/`)
  7. Run test suite (`pytest --cov=src`)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///data/resalelens.db` |
| `ENV` | Environment (development/production) | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `SECRET_KEY` | Application secret key | (must set in production) |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `HOST` | Server bind address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `GEMINI_API_KEY` | Google Gemini API key for AI Consultant features | (required for AI features) |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.0-flash-exp` |

**Environment File Strategy**:
- `.env.local` — Local development file with actual API keys and secrets (git-ignored)
- `.env.example` — Template file showing required variables (committed to git)
- Configuration loading order: `.env.local` (if exists), then `.env` (fallback for backward compatibility)

## Security Considerations

**Current (MVP)**:
- No authentication for public-facing features
- Admin panel will require authentication (future PR)
- Database stored locally (SQLite)

**Production (Future)**:
- Implement OAuth2 for admin authentication
- Use environment-based secrets management
- HTTPS enforcement
- Rate limiting on API endpoints
- CORS configuration for API access

## Performance Considerations

**Current Architecture**:
- Server-side rendering reduces client-side processing
- SQLite is sufficient for MVP data volumes
- Static files served directly by FastAPI

**Future Optimizations**:
- Add Redis for caching frequently accessed data
- Use CDN for static assets
- Implement database indexing on high-traffic queries
- Consider PostgreSQL connection pooling for production

## Deployment Strategy

**Development**:
- Run locally with `uvicorn --reload`
- SQLite database in `data/` directory

**Production** (Future):
- Deploy to cloud platform (e.g., Railway, Render, AWS)
- PostgreSQL managed database
- Environment variables via platform secrets
- Static files served via CDN

## Onboarding Guide for New Developers

1. **Read the PSD**: Start with `docs/psd/ResaleLens_sg_psd_v2.md` to understand the product
2. **Review the Master Plan**: Check `docs/plans/MASTER_PLAN.md` for implementation roadmap
3. **Set up local environment**: Follow README.md setup instructions
4. **Explore the codebase**: Start with `src/resalelens/main.py` to understand routing
5. **Run tests**: Execute `uv run pytest` to verify setup
6. **Make a small change**: Update a template or add a route to get familiar
7. **Use AI workflows**: Leverage `/plan_feature` and `/implement_task` for structured development

## Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **SQLAlchemy 2.0 Docs**: https://docs.sqlalchemy.org
- **HTMX Guide**: https://htmx.org/docs
- **Alembic Tutorial**: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- **uv User Guide**: https://github.com/astral-sh/uv

---

*Last updated: 2026-01-05*
