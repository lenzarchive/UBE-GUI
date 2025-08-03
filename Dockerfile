# UnityBundleExtractor - Web Interface Dockerfile
# Author: lenzarchive (https://github.com/lenzarchive)
# License: MIT License

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages (e.g., Pillow, lz4)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories at runtime
RUN mkdir -p uploads extractions logs logs/sessions static/css static/js templates

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PORT=5000
ENV WEB_CONCURRENCY=2 # Number of internal worker threads for queue processing

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check (updated path for API endpoint)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api || exit 1

# Start command (using gunicorn for production)
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "-w", "${MAX_WORKERS}", "--timeout", "${WORKER_TIMEOUT}", "wsgi:application"]