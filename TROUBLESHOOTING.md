# Troubleshooting Guide

This guide helps you resolve common issues with the CFC RAG Service deployment.

## Common Issues

### 1. Health Check Failures

**Symptoms:**
- `[PR03] could not find a good candidate within 20 attempts at load balancing`
- `no known healthy instances found for route tcp/443`

**Solutions:**

1. **Check application logs:**
   ```bash
   fly logs --since 10m
   ```

2. **Check if the app is running:**
   ```bash
   fly status
   ```

3. **Restart the application:**
   ```bash
   fly apps restart sermon-rag
   ```

4. **Scale down and up:**
   ```bash
   fly scale count 0
   sleep 10
   fly scale count 1
   ```

### 2. Out of Memory (OOM) Errors

**Symptoms:**
- Application crashes during startup
- Gunicorn workers killed
- Memory usage spikes

**Solutions:**

1. **Check current memory allocation:**
   ```bash
   fly status
   ```

2. **Increase memory if needed:**
   ```bash
   fly scale memory 8192
   ```

3. **Reduce worker count:**
   - The current configuration uses 1 worker to minimize memory usage
   - Check `start.sh` for current settings

### 3. RAG Service Initialization Issues

**Symptoms:**
- Application starts but RAG queries fail
- Vectorstore not found errors

**Solutions:**

1. **Check vectorstore status:**
   ```bash
   fly ssh console -C "python manage.py check_vectorstore"
   ```

2. **Initialize vectorstore manually:**
   ```bash
   fly ssh console -C "python manage.py init_vectorstore"
   ```

3. **Check dataset availability:**
   ```bash
   fly ssh console -C "ls -la /app/dataset/"
   ```

### 4. Database Issues

**Symptoms:**
- Migration errors
- Database connection failures

**Solutions:**

1. **Run migrations:**
   ```bash
   fly ssh console -C "python manage.py migrate"
   ```

2. **Check database status:**
   ```bash
   fly ssh console -C "python manage.py dbshell"
   ```

### 5. Environment Variable Issues

**Symptoms:**
- API key errors
- Configuration not found

**Solutions:**

1. **Check current secrets:**
   ```bash
   fly secrets list
   ```

2. **Set missing secrets:**
   ```bash
   fly secrets set GOOGLE_API_KEY="your-api-key"
   fly secrets set DJANGO_SECRET_KEY="your-secret-key"
   fly secrets set DJANGO_DEBUG="False"
   ```

## Debugging Commands

### View Logs
```bash
# Recent logs
fly logs --since 5m

# Follow logs in real-time
fly logs --follow

# Logs from specific time
fly logs --since 2024-01-01T10:00:00Z
```

### Check Application Status
```bash
# App status
fly status

# Health check
curl https://sermon-rag.fly.dev/health/

# Detailed health check
curl https://sermon-rag.fly.dev/health/detailed/

# Status endpoint
curl https://sermon-rag.fly.dev/status/
```

### Access Application Console
```bash
# SSH into the app
fly ssh console

# Run commands directly
fly ssh console -C "python manage.py check"
fly ssh console -C "python test_startup.py"
```

### Scaling and Restart
```bash
# Restart the app
fly apps restart sermon-rag

# Scale to 0 instances (stop)
fly scale count 0

# Scale to 1 instance (start)
fly scale count 1

# Scale memory
fly scale memory 8192
```

## Performance Optimization

### Memory Usage
- Current configuration: 8GB RAM, 4 CPUs
- Single Gunicorn worker to minimize memory usage
- Lazy loading of RAG components

### Startup Time
- Vectorstore initialization can take 5-10 minutes
- Health checks have 180s grace period
- Use `fly logs --follow` to monitor startup progress

### Monitoring
```bash
# Monitor resource usage
fly status

# Check logs for errors
fly logs --since 1h | grep -i error

# Test health endpoints
curl -f https://sermon-rag.fly.dev/health/
```

## Emergency Procedures

### Complete Reset
If the application is completely broken:

1. **Destroy and recreate:**
   ```bash
   fly apps destroy sermon-rag --yes
   ./deploy.sh
   ```

2. **Or restart from scratch:**
   ```bash
   fly scale count 0
   sleep 30
   fly scale count 1
   ```

### Data Recovery
- Vectorstore is stored in `/app/vectorstore/`
- Database is in `/app/data/`
- Logs are in `/app/logs/`

## Getting Help

1. **Check logs first:** `fly logs --since 10m`
2. **Test locally:** Run `python test_startup.py`
3. **Check configuration:** Verify `fly.toml` and environment variables
4. **Monitor resources:** Use `fly status` to check resource usage

## Prevention

1. **Regular monitoring:** Check logs and status regularly
2. **Resource monitoring:** Watch memory and CPU usage
3. **Backup strategy:** Consider backing up vectorstore and database
4. **Testing:** Test changes locally before deploying 