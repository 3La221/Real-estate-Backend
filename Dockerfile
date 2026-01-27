# Docker Configuration (Optional)
# Uncomment and customize if you want to use Docker

# FROM python:3.11-slim

# ENV PYTHONUNBUFFERED=1
# ENV PYTHONDONTWRITEBYTECODE=1

# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     postgresql-client \
#     build-essential \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Install Python dependencies
# COPY requirements/production.txt requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy project
# COPY . .

# # Collect static files
# RUN python manage.py collectstatic --noinput

# # Run gunicorn
# CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
