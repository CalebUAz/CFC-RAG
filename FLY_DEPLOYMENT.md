# Fly.io Deployment Guide for Sermon RAG

This guide will help you deploy your Django RAG application to Fly.io with production-ready configurations.

## Prerequisites

1. **Fly.io CLI**: Install the Fly CLI
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Fly.io Account**: Sign up at [fly.io](https://fly.io) and authenticate
   ```bash
   fly auth login
   ```

3. **Docker**: Ensure Docker is installed and running

## Initial Setup

### 1. Create the Fly App

```bash
# Navigate to your project directory
cd CFC-RAG

# Create the Fly app (replace 'sermon-rag' with your preferred app name)
fly apps create sermon-rag
```

### 2. Create Volume for Persistent Data

```bash
# Create a volume for your data (replace 'iad' with your preferred region)
fly volumes create sermon_data --size 10 --region iad
```

### 3. Set Environment Variables

```bash
# Set your Google API key
fly secrets set GOOGLE_API_KEY="your-google-api-key-here"

# Set Django secret key
fly secrets set SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"

# Set other environment variables
fly secrets set DEBUG="False"
fly secrets set ALLOWED_HOSTS="sermon-rag.fly.dev,*.fly.dev,*.fly.io"
```

### 4. Deploy the Application

```bash
# Deploy to Fly.io
fly deploy
```

## Configuration Files

### fly.toml
The `fly.toml` file is already configured with:
- **App name**: `sermon-rag`
- **Primary region**: `iad` (Virginia)
- **VM resources**: 1 CPU, 2GB RAM
- **Health checks**: HTTP checks on `/health/`
- **Auto-scaling**: Enabled with 0 minimum machines
- **HTTPS**: Forced HTTPS with automatic SSL

### Dockerfile
The production Dockerfile includes:
- **Security**: Non-root user execution
- **Optimization**: Multi-stage build considerations
- **Health checks**: Built-in health monitoring
- **Performance**: Optimized Gunicorn settings

### Django Settings
Production settings include:
- **Security headers**: HSTS, XSS protection, content type sniffing
- **HTTPS redirect**: Automatic SSL redirection
- **CORS**: Proper cross-origin configuration
- **Logging**: File and console logging
- **Static files**: WhiteNoise for serving static files

## Deployment Commands

### Basic Deployment
```bash
# Deploy the application
fly deploy

# Check deployment status
fly status

# View logs
fly logs
```

### Scaling and Management
```bash
# Scale the application
fly scale count 2

# Scale memory
fly scale memory 4096

# Scale CPU
fly scale cpu 2

# View current scale
fly scale show
```

### Monitoring and Debugging
```bash
# View application logs
fly logs

# SSH into the application
fly ssh console

# Check application health
fly status

# View metrics
fly dashboard
```

## Environment Variables

### Required Variables
```bash
# Set these in Fly.io secrets
fly secrets set GOOGLE_API_KEY="your-google-api-key"
fly secrets set SECRET_KEY="your-django-secret-key"
fly secrets set DEBUG="False"
fly secrets set ALLOWED_HOSTS="sermon-rag.fly.dev,*.fly.dev,*.fly.io"
```

### Optional Variables
```bash
# For additional monitoring
fly secrets set SENTRY_DSN="your-sentry-dsn"

# For Redis (if using Celery)
fly secrets set REDIS_URL="redis://your-redis-url"
```

## Data Management

### Persistent Storage
The application uses Fly.io volumes for persistent data:
- **Database**: SQLite stored in `/app/data/`
- **Vectorstore**: FAISS index stored in `/app/vectorstore/`
- **Logs**: Application logs stored in `/app/logs/`

### Backup Strategy
```bash
# Create a backup of your volume
fly volumes create sermon_data_backup --size 10 --region iad

# You can also use Fly.io's built-in backup features
fly volumes list
```

## Performance Optimization

### Resource Allocation
The current configuration uses:
- **CPU**: 1 shared CPU
- **Memory**: 2GB RAM
- **Storage**: 10GB volume

### Scaling Recommendations
- **Low traffic**: 1 CPU, 2GB RAM
- **Medium traffic**: 2 CPU, 4GB RAM
- **High traffic**: 4 CPU, 8GB RAM

### Auto-scaling
The application is configured with auto-scaling:
- **Min machines**: 0 (scales to zero when not in use)
- **Max machines**: Unlimited (based on your plan)
- **Scaling triggers**: Based on HTTP requests

## Security Considerations

### HTTPS
- **Automatic SSL**: Fly.io provides automatic SSL certificates
- **HSTS**: HTTP Strict Transport Security enabled
- **Secure headers**: XSS protection, content type sniffing prevention

### Environment Variables
- **Secrets**: Sensitive data stored in Fly.io secrets
- **No hardcoded values**: All sensitive data externalized

### CORS
- **Production**: Restricted to Fly.io domains
- **Development**: Open for local development

## Monitoring and Logging

### Built-in Monitoring
- **Health checks**: Automatic health monitoring
- **Metrics**: Available in Fly.io dashboard
- **Logs**: Centralized logging

### External Monitoring (Optional)
```bash
# Set up Sentry for error tracking
fly secrets set SENTRY_DSN="your-sentry-dsn"
```

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   ```bash
   # Check logs
   fly logs
   
   # Check status
   fly status
   
   # Rebuild and deploy
   fly deploy --force
   ```

2. **Application Not Starting**
   ```bash
   # Check environment variables
   fly secrets list
   
   # SSH into the app
   fly ssh console
   
   # Check logs
   fly logs
   ```

3. **Memory Issues**
   ```bash
   # Scale up memory
   fly scale memory 4096
   
   # Check memory usage
   fly status
   ```

4. **Database Issues**
   ```bash
   # Check volume status
   fly volumes list
   
   # SSH into app and check database
   fly ssh console
   ls -la /app/data/
   ```

### Debug Commands
```bash
# View detailed logs
fly logs --all

# Check app configuration
fly config show

# View app info
fly info

# Check DNS
fly ips list
```

## Cost Optimization

### Fly.io Pricing
- **Free tier**: 3 shared-cpu-1x 256mb VMs, 3GB persistent volume storage
- **Paid plans**: Pay-as-you-go pricing

### Cost Optimization Tips
1. **Use shared CPU**: More cost-effective for most workloads
2. **Scale to zero**: Enable auto-scaling to minimize costs
3. **Monitor usage**: Use Fly.io dashboard to track resource usage
4. **Optimize resources**: Right-size your VM specifications

## Next Steps

1. **Deploy**: Run `fly deploy` to deploy your application
2. **Test**: Verify the application is working correctly
3. **Monitor**: Set up monitoring and alerting
4. **Optimize**: Monitor performance and optimize as needed
5. **Scale**: Scale resources based on usage patterns

## Support

- **Fly.io Documentation**: [docs.fly.io](https://docs.fly.io)
- **Fly.io Community**: [community.fly.io](https://community.fly.io)
- **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com)

Your Django RAG application is now ready for production deployment on Fly.io! 🚀 