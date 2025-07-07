# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8000
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libgomp1 \
        && rm -rf /var/lib/apt/lists/* \
        && apt-get clean

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p staticfiles vectorstore data logs dataset \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check - more lenient for RAG service initialization
HEALTHCHECK --interval=60s --timeout=30s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run the application with production settings
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "300", "--max-requests", "1000", "--max-requests-jitter", "100", "--worker-class", "sync", "--preload", "sermon_rag.wsgi:application"]
