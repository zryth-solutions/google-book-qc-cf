# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY rag_ingestion_service/requirements.txt ./requirements.txt

# Install Python dependencies (without spaCy model)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY rag_ingestion_service/ .
COPY utils/ ./utils

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port (Cloud Run will override this)
EXPOSE 8080

# Default command - run CLI main for Cloud Run Job
CMD ["python", "cli_main.py"]