#!/bin/bash

# Fly.io Deployment Script for Sermon RAG
# This script automates the deployment process to Fly.io

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate environment
validate_environment() {
    print_status "Validating environment..."
    
    # Check if fly CLI is installed
    if ! command_exists fly; then
        print_error "Fly CLI is not installed. Please install it first:"
        echo "  macOS: brew install flyctl"
        echo "  Linux: curl -L https://fly.io/install.sh | sh"
        echo "  Windows: powershell -Command \"iwr https://fly.io/install.ps1 -useb | iex\""
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "fly.toml" ]; then
        print_error "fly.toml not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration before deploying."
        else
            print_error ".env.example not found. Please create a .env file with your configuration."
            exit 1
        fi
    fi
    
    print_success "Environment validation completed."
}

# Function to check if app exists
check_app_exists() {
    local app_name=$1
    fly apps list | grep -q "$app_name" 2>/dev/null || return 1
}

# Function to create app if it doesn't exist
create_app() {
    local app_name=$1
    local region=${2:-"iad"}
    
    print_status "Checking if app '$app_name' exists..."
    
    if check_app_exists "$app_name"; then
        print_success "App '$app_name' already exists."
    else
        print_status "Creating app '$app_name' in region '$region'..."
        fly apps create "$app_name" --org personal
        print_success "App '$app_name' created successfully."
    fi
}

# Function to create volume if it doesn't exist
create_volume() {
    local app_name=$1
    local volume_name="sermon_data"
    local region=${2:-"iad"}
    local size=${3:-"10"}
    
    print_status "Checking if volume '$volume_name' exists..."
    
    if fly volumes list --app "$app_name" | grep -q "$volume_name" 2>/dev/null; then
        print_success "Volume '$volume_name' already exists."
    else
        print_status "Creating volume '$volume_name' (${size}GB) in region '$region'..."
        fly volumes create "$volume_name" --size "$size" --region "$region" --app "$app_name"
        print_success "Volume '$volume_name' created successfully."
    fi
}

# Function to set secrets
set_secrets() {
    local app_name=$1
    
    print_status "Setting up secrets for app '$app_name'..."
    
    # Check if secrets are already set
    local secrets_count=$(fly secrets list --app "$app_name" 2>/dev/null | wc -l)
    
    if [ "$secrets_count" -gt 1 ]; then
        print_warning "Secrets already exist. Skipping secret setup."
        print_warning "To update secrets, run: fly secrets set KEY=VALUE --app $app_name"
        return 0
    fi
    
    # Load environment variables from .env file
    if [ -f ".env" ]; then
        print_status "Loading secrets from .env file..."
        
        # Read .env file and set secrets
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ $key =~ ^#.*$ ]] && continue
            [[ -z $key ]] && continue
            
            # Remove quotes from value
            value=$(echo "$value" | sed 's/^"//;s/"$//;s/^'"'"'//;s/'"'"'$//')
            
            # Skip if value is empty
            [[ -z $value ]] && continue
            
            print_status "Setting secret: $key"
            fly secrets set "$key=$value" --app "$app_name" --yes
        done < .env
        
        print_success "Secrets loaded from .env file."
    else
        print_warning "No .env file found. Please set secrets manually:"
        echo "  fly secrets set GOOGLE_API_KEY=your-key --app $app_name"
        echo "  fly secrets set SECRET_KEY=your-secret --app $app_name"
        echo "  fly secrets set DEBUG=False --app $app_name"
        echo "  fly secrets set ALLOWED_HOSTS=sermon-rag.fly.dev,*.fly.dev,*.fly.io --app $app_name"
    fi
}

# Function to deploy the application
deploy_app() {
    local app_name=$1
    
    print_status "Deploying application '$app_name' to Fly.io..."
    
    # Build and deploy
    fly deploy --app "$app_name"
    
    print_success "Deployment completed successfully!"
}

# Function to check deployment status
check_deployment() {
    local app_name=$1
    
    print_status "Checking deployment status..."
    
    # Wait a moment for deployment to settle
    sleep 5
    
    # Check app status
    fly status --app "$app_name"
    
    # Check if app is running
    if fly status --app "$app_name" | grep -q "running"; then
        print_success "Application is running successfully!"
        
        # Get the app URL
        local app_url=$(fly status --app "$app_name" | grep "Hostname" | awk '{print $2}')
        if [ -n "$app_url" ]; then
            print_success "Your application is available at: https://$app_url"
        fi
    else
        print_error "Application deployment may have failed. Check logs with: fly logs --app $app_name"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --app-name NAME     App name (default: sermon-rag)"
    echo "  -r, --region REGION     Region (default: iad)"
    echo "  -s, --volume-size SIZE  Volume size in GB (default: 10)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Deploy with default settings"
    echo "  $0 -a my-sermon-app                   # Deploy with custom app name"
    echo "  $0 -a my-app -r syd -s 20            # Deploy with custom settings"
}

# Main function
main() {
    # Default values
    APP_NAME="sermon-rag"
    REGION="iad"
    VOLUME_SIZE="10"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--app-name)
                APP_NAME="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -s|--volume-size)
                VOLUME_SIZE="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Starting Fly.io deployment for Sermon RAG..."
    print_status "App name: $APP_NAME"
    print_status "Region: $REGION"
    print_status "Volume size: ${VOLUME_SIZE}GB"
    echo ""
    
    # Validate environment
    validate_environment
    
    # Create app if it doesn't exist
    create_app "$APP_NAME" "$REGION"
    
    # Create volume if it doesn't exist
    create_volume "$APP_NAME" "$REGION" "$VOLUME_SIZE"
    
    # Set secrets
    set_secrets "$APP_NAME"
    
    # Deploy the application
    deploy_app "$APP_NAME"
    
    # Check deployment status
    check_deployment "$APP_NAME"
    
    echo ""
    print_success "Deployment completed successfully! 🚀"
    print_status "Next steps:"
    echo "  1. Test your application at the provided URL"
    echo "  2. Monitor logs: fly logs --app $APP_NAME"
    echo "  3. Check status: fly status --app $APP_NAME"
    echo "  4. Scale if needed: fly scale count 2 --app $APP_NAME"
}

# Run main function with all arguments
main "$@" 