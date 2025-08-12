FROM python:3.11-slim

WORKDIR /app

# Install only what's needed for dashboard
COPY requirements.dashboard.txt .
RUN pip install --no-cache-dir -r requirements.dashboard.txt

# Copy only necessary files
COPY dashboard.py .
COPY .env .
COPY meta.json .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "dashboard.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]