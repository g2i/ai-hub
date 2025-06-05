# Celery Redis Connection Troubleshooting Guide

## Problem Summary
You're experiencing connection timeouts and broken pipe errors when running Celery workers with Redis on Railway.

## Solutions Applied

### 1. Enhanced Celery Configuration
Updated `app/core/celery_app.py` with:
- Connection retry settings
- Socket keepalive options
- Proper timeout configurations
- Worker settings to handle connection loss gracefully

### 2. Testing Tools Created

#### Test Redis Connection
```bash
python test_redis_connection.py
```
This script will:
- Test basic connectivity
- Verify read/write operations
- Check connection stability
- Test pub/sub functionality
- Validate connection pooling

#### Run Celery Worker with Enhanced Options
```bash
./run_celery_worker.sh
```
This script runs Celery with:
- Disabled gossip, mingle, and heartbeat (reduces connection overhead)
- Fair task distribution
- Proper concurrency and task limits

## Troubleshooting Steps

### 1. Verify Redis Connection
First, ensure your Redis connection is working:
```bash
export REDIS_CONN_STRING="redis://default:password@turntable.proxy.rlwy.net:16476/"
python test_redis_connection.py
```

### 2. Check Network Connectivity
If the connection test fails:
```bash
# Test DNS resolution
nslookup turntable.proxy.rlwy.net

# Test port connectivity
nc -zv turntable.proxy.rlwy.net 16476

# Test with redis-cli
redis-cli -u $REDIS_CONN_STRING ping
```

### 3. Run Celery with Minimal Configuration
If issues persist, try running with minimal workers:
```bash
celery -A app.core.celery_app worker --loglevel=DEBUG --concurrency=1
```

### 4. Alternative Celery Start Commands

#### For Development (with auto-reload):
```bash
celery -A app.core.celery_app worker --loglevel=INFO --autoreload
```

#### For Production (with systemd):
Create `/etc/systemd/system/celery.service`:
```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=your-user
Group=your-group
EnvironmentFile=/path/to/env/file
WorkingDirectory=/path/to/api-proxy
ExecStart=/path/to/venv/bin/celery -A app.core.celery_app worker --detach
ExecStop=/path/to/venv/bin/celery -A app.core.celery_app control shutdown
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Monitor Redis Connection
```bash
# Watch Redis info in real-time
watch -n 1 'redis-cli -u $REDIS_CONN_STRING info clients'

# Monitor Celery events
celery -A app.core.celery_app events
```

## Common Issues and Solutions

### Issue: "Timeout reading from socket"
**Cause**: Network latency or Redis server overload
**Solution**: 
- Increase socket timeout in configuration
- Use connection pooling
- Consider using Redis Sentinel or Cluster for HA

### Issue: "Broken pipe"
**Cause**: Connection dropped due to inactivity or network issues
**Solution**:
- Enable socket keepalive (already configured)
- Reduce worker prefetch count
- Use `--without-gossip --without-mingle --without-heartbeat`

### Issue: "Connection to broker lost"
**Cause**: Intermittent network issues
**Solution**:
- Enable connection retry (already configured)
- Use persistent connections
- Consider using a local Redis instance for development

## Railway-Specific Considerations

1. **Internal Networking**: If running Celery on Railway, use internal URLs:
   ```
   redis://default:password@redis.railway.internal:6379
   ```

2. **Connection Limits**: Railway Redis instances may have connection limits. Monitor with:
   ```bash
   redis-cli -u $REDIS_CONN_STRING config get maxclients
   ```

3. **Timeout Settings**: Railway may have proxy timeouts. Keep connections active with keepalive.

## Performance Optimization

1. **Use Connection Pooling**:
   ```python
   # Already configured in celery_app.py
   ```

2. **Batch Operations**:
   ```python
   # Use pipeline for multiple operations
   with redis_client.pipeline() as pipe:
       pipe.set('key1', 'value1')
       pipe.set('key2', 'value2')
       pipe.execute()
   ```

3. **Monitor Memory Usage**:
   ```bash
   redis-cli -u $REDIS_CONN_STRING info memory
   ```

## Next Steps

1. Run the connection test script to diagnose the issue
2. Use the enhanced Celery worker script
3. Monitor logs for any new error patterns
4. Consider implementing a Redis connection pool manager if issues persist

## Additional Resources

- [Celery Redis Transport Docs](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html)
- [Redis Connection Pooling](https://redis-py.readthedocs.io/en/stable/connections.html)
- [Railway Redis Guide](https://docs.railway.app/databases/redis) 