FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --settings=erms_project.settings

# Create media directory
RUN mkdir -p /app/media

EXPOSE 8000

CMD ["gunicorn", "erms_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
