#!/bin/bash

# Production deployment script for CFC RAG Service
# This script deploys the application to Fly.io with proper configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    print_error "Fly CLI is not installed. Please install it first:"
    echo "curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if we're logged in to Fly.io
if ! fly auth whoami &> /dev/null; then
    print_error "Not logged in to Fly.io. Please run: fly auth login"
    exit 1
fi

print_status "Starting deployment of CFC RAG Service..."

# Check if app exists, create if not
if ! fly apps list | grep -q "sermon-rag"; then
    print_status "Creating new Fly.io app..."
    fly apps create sermon-rag --org personal
    print_success "App created successfully!"
else
    print_status "App already exists"
fi

# Set secrets if not already set
print_status "Setting up secrets..."
if ! fly secrets list | grep -q "GOOGLE_API_KEY"; then
    if [ -z "$GOOGLE_API_KEY" ]; then
        print_error "GOOGLE_API_KEY environment variable is not set"
        echo "Please set it: export GOOGLE_API_KEY=your_api_key"
        exit 1
    fi
    fly secrets set GOOGLE_API_KEY="$GOOGLE_API_KEY"
    print_success "GOOGLE_API_KEY secret set"
else
    print_status "GOOGLE_API_KEY secret already exists"
fi

# Set Django secret key if not already set
if ! fly secrets list | grep -q "DJANGO_SECRET_KEY"; then
    DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    fly secrets set DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY"
    print_success "DJANGO_SECRET_KEY secret set"
else
    print_status "DJANGO_SECRET_KEY secret already exists"
fi

# Set debug mode to false for production
if ! fly secrets list | grep -q "DJANGO_DEBUG"; then
    fly secrets set DJANGO_DEBUG="False"
    print_success "DJANGO_DEBUG secret set to False"
else
    print_status "DJANGO_DEBUG secret already exists"
fi

# Deploy the application
print_status "Deploying application..."
fly deploy --remote-only

# Wait for deployment to complete
print_status "Waiting for deployment to complete..."
sleep 30

# Check deployment status
print_status "Checking deployment status..."
if fly status | grep -q "running"; then
    print_success "Deployment completed successfully!"
else
    print_error "Deployment failed or app is not running"
    print_status "Checking logs for more information..."
    fly logs --since 5m
    exit 1
fi

# Check application health
print_status "Checking application health..."
health_check_passed=false
for i in {1..60}; do
    if curl -f https://sermon-rag.fly.dev/health/ >/dev/null 2>&1; then
        print_success "Application is healthy!"
        health_check_passed=true
        break
    else
        print_warning "Health check attempt $i/60 failed, retrying in 10 seconds..."
        sleep 10
    fi
done

if [ "$health_check_passed" = false ]; then
    print_error "Health check failed after 60 attempts"
    print_status "Checking recent logs..."
    fly logs --since 10m
    exit 1
fi

# Check detailed health
print_status "Checking detailed health status..."
if curl -f https://sermon-rag.fly.dev/health/detailed/ >/dev/null 2>&1; then
    print_success "Detailed health check passed!"
else
    print_warning "Detailed health check failed, but basic health check passed"
fi

# Display final status
print_success "Deployment completed successfully!"
echo ""
echo "🌐 Application URL: https://sermon-rag.fly.dev"
echo "📊 Health Check: https://sermon-rag.fly.dev/health/"
echo "🔍 Status Check: https://sermon-rag.fly.dev/status/"
echo ""
echo "📝 Useful commands:"
echo "  fly logs                    # View application logs"
echo "  fly status                  # Check app status"
echo "  fly ssh console             # Access app console"
echo "  fly scale count 0           # Scale down to 0 instances"
echo "  fly scale count 1           # Scale up to 1 instance"
echo ""
print_success "Your CFC RAG Service is now live! 🎉" 