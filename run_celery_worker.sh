#!/bin/bash

# Script to run Celery worker with enhanced logging and debugging

echo "🚀 Starting Celery worker with enhanced configuration..."

# Check if REDIS_CONN_STRING is set
if [ -z "$REDIS_CONN_STRING" ]; then
    echo "❌ Error: REDIS_CONN_STRING environment variable is not set!"
    echo "Please set it using: export REDIS_CONN_STRING='your-redis-url'"
    exit 1
fi

echo "📡 Redis URL: ${REDIS_CONN_STRING//:*@/:***@}"

# Run Celery worker with enhanced options
celery -A app.core.celery_app worker \
    --loglevel=INFO \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    --time-limit=300 \
    --soft-time-limit=240 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat \
    -E \
    --pool=prefork \
    -Ofair 