FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pandas/numpy and health check
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY dashboard.py .
COPY auth_config.py .

# Copy image assets
COPY favicon.png .
COPY loader.gif .
COPY logo.png .

# Don't copy sensitive files - these should be provided via environment variables
# meta.json and .env should NOT be in the Docker image

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run uses PORT environment variable
ENV PORT=8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

# Run Streamlit on the PORT provided by Cloud Run
CMD streamlit run dashboard.py \
     --server.port=${PORT} \
     --server.address=0.0.0.0 \
     --server.headless=true \
     --browser.gatherUsageStats=false \
     --theme.base=dark \
     --theme.primaryColor=#4da3ff