# Use Python 3.11 alpine for smaller size
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies in a single layer
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    && apk add --no-cache \
    libffi-dev \
    && pip install --no-cache-dir --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies and remove build dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps \
    && rm -rf /root/.cache/pip

# Copy source code and project metadata for editable install
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install the package itself so 'glean_mcp' is on PYTHONPATH
RUN pip install --no-cache-dir . \
    && rm -rf /root/.cache/pip

# Create a non-root user (alpine style)
RUN adduser -D -s /bin/sh mcp-user \
    && chown -R mcp-user:mcp-user /app
USER mcp-user

# Health check (simplified)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command - execute server module (installed entry context)
CMD ["python", "-m", "glean_mcp.server"]
