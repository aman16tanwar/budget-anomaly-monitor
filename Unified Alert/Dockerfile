# Dockerfile for Unified Budget Monitoring Cloud Run Jobs
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files at once (simpler approach)
COPY *.py ./
COPY *.json ./
COPY *.csv ./
COPY *.sql ./
COPY images/ ./images/

# Create non-root user for security  
RUN useradd -m -u 1000 jobuser && chown -R jobuser:jobuser /app
USER jobuser

# Set environment variable for Google Application Credentials
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/meta.json

# Default entrypoint for unified monitoring
CMD ["python", "unified_budget_monitoring_job.py"]