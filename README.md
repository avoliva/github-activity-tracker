# GitHub Activity Tracker API

A FastAPI-based REST API for analyzing GitHub user activity. The API fetches user events from GitHub and provides insights about their top activity types per repository.

## Description

This API analyzes GitHub user activity by:
- Fetching user events from the GitHub REST API
- Grouping events by repository
- Identifying the top 3 activity types per repository
- Determining repository ownership

The API includes in-memory caching for improved performance and comprehensive error handling.

## Installation

### Prerequisites

- Python 3.9 or higher (for direct Python)
- Docker (for Docker deployment)
- pip

### Setup

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development tools
   ```

3. **Configure environment variables (optional):**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` if you need to customize settings. Default values work for basic usage.

4. **Run the application:**
   
   **Option A: Direct Python**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   **Option B: Docker**
   ```bash
   docker compose up
   ```
   
   The API will be available at `http://localhost:8000`

## API Reference

FastAPI automatically generates OpenAPI documentation. Once the server is running:

- **Interactive API docs (Swagger UI):** `http://localhost:8000/docs`
- **OpenAPI JSON spec:** `http://localhost:8000/openapi.json`
- **Alternative docs (ReDoc):** `http://localhost:8000/redoc`

Refer to the OpenAPI spec for complete endpoint documentation, request/response schemas, and examples.

## Testing

### Using curl

Test the main endpoint:

```bash
# Get activity for a user
curl http://localhost:8000/api/v1/users/octocat/activity

# Pretty print JSON response
curl http://localhost:8000/api/v1/users/octocat/activity | python -m json.tool
```

### Using test_local.py

The `test_local.py` script automatically starts the server and runs tests:

```bash
# Test with default user (octocat)
python test_local.py

# Test with a specific username
python test_local.py ge0ffrey

# Test against an already-running server
python test_local.py --no-start-server octocat

# Test on a different port
python test_local.py --port 9000 octocat

# Show server output for debugging
python test_local.py --debug octocat
```

### Running Tests

Run the test suite with pytest:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_services.py

# Run with verbose output
pytest -v
```

## Development

### Project Structure

```
app/
├── api/              # API routes and router
├── core/             # Configuration and dependencies
├── models/           # Pydantic models and schemas
├── repositories/     # Data access layer
├── services/         # Business logic
└── utils/            # Utility functions (cache, etc.)
tests/
├── unit/             # Unit tests
└── integration/      # Integration tests
```

### Code Quality

The project uses several tools for code quality:

- **ruff**: Linting and formatting
- **mypy**: Type checking
- **black**: Code formatting (configured in pyproject.toml)
- **pytest**: Testing framework

Run linting and type checking:

```bash
ruff check .
mypy app
```

### Environment Variables

See `.env.example` for available configuration options. Key settings:

- `API_HOST`: Server host (default: `0.0.0.0`)
- `API_PORT`: Server port (default: `8000`)
- `GITHUB_API_BASE_URL`: GitHub API base URL (default: `https://api.github.com`)
- `CACHE_TTL_SECONDS`: Cache TTL in seconds (default: `600`)
- `CACHE_MAX_SIZE`: Maximum cache entries (default: `1000`)
- `REQUEST_TIMEOUT_SECONDS`: HTTP request timeout (default: `30`)
- `DEBUG`: Enable debug mode (default: `false`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

