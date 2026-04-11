#!/bin/bash
set -e

echo "======================================"
echo "Real Estate API - Docker Entrypoint"
echo "======================================"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.5
done
echo "Redis is ready!"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create logs directory if it doesn't exist
mkdir -p logs

echo "======================================"
echo "Starting application..."
echo "======================================"

# Execute the command passed to the script
exec "$@"
