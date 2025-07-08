#!/bin/bash

# Production startup script for CFC RAG Service
# This script starts the Django application with Gunicorn

set -e

echo "🚀 Starting CFC RAG Service..."

# Set environment variables
export DJANGO_SETTINGS_MODULE=sermon_rag.settings
export PYTHONPATH=/app

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Function to check if the application is ready
check_ready() {
    echo "🔍 Checking if application is ready..."
    
    # Wait for database migrations
    echo "📊 Running database migrations..."
    python manage.py migrate --noinput
    
    # Check if vectorstore exists, if not initialize it
    if [ ! -f "/app/vectorstore/index.faiss" ]; then
        echo "📚 Vectorstore not found. Initializing..."
        python manage.py init_vectorstore
    else
        echo "✅ Vectorstore found"
    fi
    
    # Test basic Django functionality
    echo "🧪 Testing Django application..."
    python manage.py check --deploy
    
    echo "✅ Application is ready!"
}

# Function to start Gunicorn
start_gunicorn() {
    echo "🔄 Starting Gunicorn server..."
    
    # Memory-optimized settings for production
    exec gunicorn \
        --bind 0.0.0.0:8000 \
        --workers 1 \
        --worker-class sync \
        --worker-connections 50 \
        --max-requests 25 \
        --max-requests-jitter 5 \
        --timeout 120 \
        --keep-alive 2 \
        --preload \
        --access-logfile /app/logs/access.log \
        --error-logfile /app/logs/error.log \
        --log-level info \
        --capture-output \
        --max-requests-jitter 5 \
        sermon_rag.wsgi:application
}

# Main execution
echo "🔧 Setting up application..."

# Check if application is ready
check_ready

# Start the server
start_gunicorn
