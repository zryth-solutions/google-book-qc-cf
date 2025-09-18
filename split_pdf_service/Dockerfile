# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements.txt

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy service-specific code
COPY split_pdf_service/ .

# Copy utils directory
COPY utils/ ./utils

# Create necessary directories
RUN mkdir -p /tmp/pdf_processing

# Set environment variables
ENV PYTHONPATH=/app

# Run the CLI application
ENTRYPOINT ["python", "cli_main.py"]
