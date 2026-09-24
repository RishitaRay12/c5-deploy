# 1. Use an official Python 3.12 standard image (needed for C-extensions like faiss, numpy, psycopg)
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system-level dependencies required for building C extensions (e.g. pgvector, psycopg, faiss)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Install 'uv' for ultra-fast dependency resolution and installation
RUN pip install --no-cache-dir uv

# Copy configuration files first to leverage Docker layer caching
COPY pyproject.toml ./
COPY README.md ./

# Install project dependencies directly into the system Python environment
RUN uv pip install --system .

# Copy the rest of your application code
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Start application using Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
