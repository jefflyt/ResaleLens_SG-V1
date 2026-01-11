# Contributing to ResaleLens SG

Thank you for contributing to ResaleLens SG! This guide will help you get started.

## Development Setup

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Supabase account with project created

### Installation
```bash
# Clone repository
git clone <repository-url>
cd ResaleLens_SG-V1

# Install dependencies
uv sync

# Set up environment
cp .env.example .env.local
# Edit .env.local with your Supabase connection string

# Run migrations
uv run alembic upgrade head
```

---

## Testing Strategy

### Test Database Architecture

ResaleLens uses a **dual-database testing strategy** for optimal development experience:

#### Application Code
- **Always uses Supabase PostgreSQL** via `DATABASE_URL` environment variable
- Ensures development environment matches production exactly
- No database-specific bugs or surprises

#### Test Suite
- **Uses SQLite in-memory** for fast execution
- Configured in `tests/conftest.py`
- **10-100x faster** than PostgreSQL tests
- No cleanup needed (database destroyed after each test)
- SQLAlchemy abstracts database differences well

### Why SQLite for Tests?

**Speed:**
- Full test suite runs in ~8 seconds with SQLite
- Same tests would take 2-5 minutes with PostgreSQL
- Faster feedback loop during development

**Isolation:**
- Each test gets a fresh in-memory database
- No state pollution between tests
- No need to clean up test data

**CI/CD:**
- No external dependencies required
- Tests run anywhere without Supabase credentials
- Faster CI pipeline

**Trade-offs:**
- PostgreSQL-specific features not tested (e.g., `INSERT ... ON CONFLICT`)
- Manual integration testing still uses Supabase

### Running Tests

```bash
# Run all tests (uses SQLite in-memory)
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_models.py -v

# Run tests matching pattern
uv run pytest -k "test_transaction" -v
```

### Test Database Configuration

The test database is configured in `tests/conftest.py`:

```python
@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    # ... session setup
```

### Manual Integration Testing

For testing PostgreSQL-specific features or real Supabase integration:

```bash
# Ensure DATABASE_URL is set to Supabase
export DATABASE_URL="postgresql://..."

# Run application
uv run uvicorn src.resalelens.main:app --reload

# Test manually via browser or curl
curl http://localhost:8000/health
```

---

## Code Quality

### Linting
```bash
# Check code style
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix
```

### Formatting
```bash
# Format code
uv run ruff format .
```

### Type Checking
```bash
# Run mypy
uv run mypy src/
```

---

## Database Migrations

### Creating Migrations
```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "Add new field to Transaction"

# Review generated migration in src/resalelens/migrations/versions/
# Edit if needed

# Apply migration
uv run alembic upgrade head
```

### Migration Best Practices
- Always review auto-generated migrations
- Test migrations on development database first
- Include both `upgrade()` and `downgrade()` functions
- Use descriptive migration messages

---

## Pull Request Guidelines

### Before Submitting
- [ ] All tests pass (`uv run pytest`)
- [ ] Code is formatted (`uv run ruff format .`)
- [ ] No linting errors (`uv run ruff check .`)
- [ ] Type checking passes (`uv run mypy src/`)
- [ ] Documentation updated if needed

### PR Description
- Describe what changed and why
- Link to related issues or plans
- Include screenshots for UI changes
- List any breaking changes

---

## Project Structure

```
ResaleLens_SG-V1/
├── src/resalelens/          # Application code
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # SQLAlchemy ORM models
│   ├── database.py          # Database setup
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic
│   ├── ingestion/           # Data ingestion modules
│   └── migrations/          # Alembic migrations
├── tests/                   # Test suite (SQLite in-memory)
│   ├── conftest.py          # Test fixtures and config
│   ├── test_models.py       # Model tests
│   └── ingestion/           # Ingestion tests
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JS, images
├── scripts/                 # Utility scripts
└── docs/                    # Documentation
```

---

## Getting Help

- Check existing documentation in `docs/`
- Review plan documents in `docs/plans/`
- Ask questions in pull requests
- Check Supabase dashboard for database issues

---

## License

[Your License Here]
