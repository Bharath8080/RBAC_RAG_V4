# Build stage
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir --prefer-binary -r requirements.txt

# Production stage
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/app/.local/bin:$PATH

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy application code
COPY --chown=app:app . .

USER app

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
