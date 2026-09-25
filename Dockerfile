FROM python:3.11-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files from backend directory
COPY backend/pyproject.toml backend/uv.lock ./

# Install project dependencies
RUN uv sync --frozen --no-cache

# Copy backend source code into workspace
COPY backend/ .

EXPOSE 8000

# Start Uvicorn via uv run
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
