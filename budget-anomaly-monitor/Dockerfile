# Dockerfile for Cloud Run Jobs
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY cloud_run_job.py .
COPY meta_api_implementation_bigquery.py .

# Create non-root user for security
RUN useradd -m -u 1000 jobuser && chown -R jobuser:jobuser /app
USER jobuser

# Set the entrypoint to run the job script
ENTRYPOINT ["python", "cloud_run_job.py"]