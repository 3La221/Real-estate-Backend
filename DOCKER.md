# Docker Deployment Guide

Production-ready Docker setup for the Real Estate Django API.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

### 1. Build and Run

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Access the Application

- **API**: http://localhost:8000/api/v1/
- **API Docs (Swagger)**: http://localhost:8000/api/docs/
- **API Docs (Redoc)**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/health/

### 3. Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

## Environment Variables

Create a `.env` file in the project root or set these in your environment:

```env
# Required
SECRET_KEY=your-super-secret-key-change-this

# Optional (defaults shown)
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Cloudinary (for media storage)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Sentry (optional)
SENTRY_DSN=https://xxx@yyy.ingest.sentry.io/zzz
```

## Services

| Service | Description | Port |
|---------|-------------|------|
| web | Django Gunicorn server | 8000 |
| redis | Redis cache & message broker | 6379 (internal) |
| celery-worker | Background task worker | - |
| celery-beat | Scheduled task scheduler | - |

## Useful Commands

```bash
# Rebuild after code changes
docker-compose up --build -d

# View specific service logs
docker-compose logs -f web
docker-compose logs -f celery-worker

# Run Django management commands
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

# Database backup/restore
docker-compose exec web python -c "import shutil; shutil.copy('db.sqlite3', 'db.sqlite3.backup')"

# Check service health
curl http://localhost:8000/api/health/

# Scale celery workers (example: 3 workers)
docker-compose up -d --scale celery-worker=3

# Clean up (removes containers, volumes, images)
docker-compose down -v --rmi all
```

## Production Deployment Checklist

- [ ] Change `SECRET_KEY` to a secure random string
- [ ] Update `ALLOWED_HOSTS` with your domain(s)
- [ ] Configure Cloudinary credentials for media storage
- [ ] Set up SMTP credentials for email
- [ ] Configure Sentry DSN for error tracking
- [ ] Use PostgreSQL instead of SQLite for production
- [ ] Set up SSL/TLS certificates
- [ ] Configure a reverse proxy (nginx/traefik)
- [ ] Set `DEBUG=False` in production settings

## Troubleshooting

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000
# Or change port in docker-compose.yml
```

### Permission denied on volumes
```bash
# Fix permissions
sudo chown -R $USER:$USER .
```

### Database locked (SQLite)
SQLite doesn't handle concurrent writes well. For production with multiple workers, switch to PostgreSQL:

1. Add to `docker-compose.yml`:
```yaml
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: realestate
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

2. Update database settings in production.py
