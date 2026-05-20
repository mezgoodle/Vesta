FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8.18 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies quickly using uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY backend /app

# Ensure we use the created virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh


# Cloud Run sets the PORT environment variable
ENV PORT 8080

ENTRYPOINT ["/app/entrypoint.sh"]

# Start uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
