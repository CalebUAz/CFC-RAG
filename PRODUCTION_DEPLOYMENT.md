# Production Deployment Guide for Sermon RAG

This guide will help you deploy your Sermon RAG application to Fly.io in a production-ready manner.

## Prerequisites

1. **Fly.io CLI installed**: `curl -L https://fly.io/install.sh | sh`
2. **Fly.io account**: Sign up at [fly.io](https://fly.io)
3. **Google API Key**: Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)
4. **Vectorstore**: Pre-built vectorstore file (optional, will be created if not present)

## 1. Environment Setup

### Create Environment File

```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your production values
nano .env
```

### Required Environment Variables

```bash
# Django Configuration
SECRET_KEY=your-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=sermon-rag.fly.dev,*.fly.dev,*.fly.io

# Google API Configuration
GOOGLE_API_KEY=your-google-api-key-here

# Optional: Sentry for error tracking
SENTRY_DSN=https://your-sentry-dsn-here

# Performance settings
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Generate a Secure Secret Key

```bash
# Generate a secure Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 2. Data Preparation

### Prepare Your Dataset

Ensure your dataset is in the correct location:
```bash
# Create dataset directory
mkdir -p dataset

# Copy your CSV file
cp your-sermon-data.csv dataset/RLCF-Pitts.csv
```

### Prepare Vectorstore (Optional)

If you have a pre-built vectorstore:
```bash
# Create vectorstore directory
mkdir -p vectorstore

# Copy your vectorstore files
cp -r your-vectorstore/* vectorstore/sermons_vectorstore/
```

## 3. Local Testing

### Test Locally with Docker

```bash
# Build the Docker image
docker build -t sermon-rag .

# Run the container
docker run -p 8000:8000 --env-file .env sermon-rag
```

### Test the Application

Visit `http://localhost:8000` to ensure everything works correctly.

## 4. Fly.io Deployment

### Initialize Fly.io App

```bash
# Login to Fly.io
fly auth login

# Create the app (if not already created)
fly apps create sermon-rag

# Set the primary region
fly config set primary_region iad
```

### Set Environment Variables

```bash
# Set production environment variables
fly secrets set SECRET_KEY="your-secret-key-here"
fly secrets set GOOGLE_API_KEY="your-google-api-key-here"
fly secrets set DEBUG="False"
fly secrets set ALLOWED_HOSTS="sermon-rag.fly.dev,*.fly.dev,*.fly.io"

# Optional: Set Sentry DSN
fly secrets set SENTRY_DSN="https://your-sentry-dsn-here"
```

### Create Persistent Volume

```bash
# Create a volume for persistent data
fly volumes create sermon_data --size 10 --region iad
```

### Deploy the Application

```bash
# Deploy to Fly.io
fly deploy

# Check deployment status
fly status
```

## 5. Post-Deployment Setup

### Initialize Vectorstore (if needed)

If you didn't include a pre-built vectorstore:

```bash
# SSH into the running container
fly ssh console

# Initialize the vectorstore (this may take several minutes)
python manage.py init_vectorstore
```

### Verify Deployment

```bash
# Check application health
fly status

# View logs
fly logs

# Open the application
fly open
```

## 6. Monitoring and Maintenance

### Health Checks

The application includes health checks at `/health/` and `/status/` endpoints.

### Logs

```bash
# View real-time logs
fly logs

# View logs for specific time period
fly logs --since 1h
```

### Scaling

```bash
# Scale the application
fly scale count 2

# Scale memory/CPU
fly scale memory 4096
fly scale cpu 2
```

### Updates

```bash
# Deploy updates
fly deploy

# Rollback if needed
fly deploy --image-label v1
```

## 7. Security Considerations

### Environment Variables

- Never commit `.env` files to version control
- Use `fly secrets` for sensitive data
- Rotate API keys regularly

### SSL/TLS

- HTTPS is automatically enabled by Fly.io
- HSTS headers are configured in production

### CORS

- CORS is configured for production domains
- Only necessary origins are allowed

## 8. Performance Optimization

### Current Configuration

- **Workers**: 2 Gunicorn workers
- **Memory**: 4GB allocated
- **CPU**: 2 shared CPUs
- **Timeout**: 300 seconds for RAG operations

### Monitoring

```bash
# Check resource usage
fly status

# Monitor performance
fly logs --follow
```

## 9. Troubleshooting

### Common Issues

1. **Vectorstore not found**
   ```bash
   # Check if vectorstore exists
   fly ssh console
   ls -la /app/vectorstore/
   ```

2. **Google API Key issues**
   ```bash
   # Verify API key is set
   fly secrets list
   ```

3. **Memory issues**
   ```bash
   # Scale up memory
   fly scale memory 8192
   ```

4. **Timeout issues**
   ```bash
   # Check logs for timeout errors
   fly logs | grep timeout
   ```

### Debug Mode

For debugging, temporarily enable debug mode:
```bash
fly secrets set DEBUG="True"
fly deploy
```

## 10. Backup and Recovery

### Database Backup

```bash
# Backup SQLite database
fly ssh console
sqlite3 /app/data/db.sqlite3 ".backup /app/data/backup.sqlite3"
```

### Vectorstore Backup

The vectorstore is stored in the persistent volume and will survive deployments.

## 11. Cost Optimization

### Auto-scaling

The application is configured with auto-scaling:
- `min_machines_running = 1`
- `auto_stop_machines = true`
- `auto_start_machines = true`

### Resource Monitoring

Monitor your usage at [fly.io dashboard](https://fly.io/dashboard).

## Support

For issues specific to Fly.io, check their [documentation](https://fly.io/docs/).

For application-specific issues, check the logs and health endpoints. 