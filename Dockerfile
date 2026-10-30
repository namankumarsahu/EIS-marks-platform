# Stage 1: Build React frontend
FROM node:22-alpine AS frontend-builder

WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# Stage 2: Production runtime
FROM nginxinc/nginx-unprivileged:alpine

USER root

# Install Python runtime and dependencies
RUN apk add --no-cache python3 py3-pip \
    && mkdir -p /app/backend /usr/share/nginx/html \
    && pip3 install --break-system-packages --no-cache-dir \
       Django==6.0.7 \
       djangorestframework==3.17.1 \
       django-cors-headers==4.9.0 \
       gunicorn

WORKDIR /app/backend

# Copy only required Django application files
COPY backend/manage.py ./
COPY backend/requirements.txt ./
COPY backend/config/ ./config/
COPY backend/core/__init__.py ./core/
COPY backend/core/apps.py ./core/
COPY backend/core/admin.py ./core/
COPY backend/core/models.py ./core/
COPY backend/core/serializers.py ./core/
COPY backend/core/services.py ./core/
COPY backend/core/views.py ./core/
COPY backend/core/urls.py ./core/
COPY backend/core/migrations/ ./core/migrations/
COPY backend/data/students_marks.csv ./data/students_marks.csv

# Apply production Django settings without embedding secrets
RUN sed -i "s/^SECRET_KEY = .*/SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')/" config/settings.py \
    && sed -i 's/^DEBUG = True$/DEBUG = False/' config/settings.py

# Copy compiled frontend
COPY --from=frontend-builder --chown=101:101 /build/dist/ /usr/share/nginx/html/

# Configure Nginx
RUN printf '%s\n' \
    'server {' \
    '    listen 0.0.0.0:3000;' \
    '    server_name _;' \
    '    root /usr/share/nginx/html;' \
    '    index index.html;' \
    '    server_tokens off;' \
    '    location /api/ {' \
    '        proxy_pass http://127.0.0.1:8000;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '    }' \
    '    location /admin/ {' \
    '        proxy_pass http://127.0.0.1:8000;' \
    '        proxy_set_header Host $host;' \
    '    }' \
    '    location / {' \
    '        try_files $uri $uri/ /index.html;' \
    '    }' \
    '    location ~ /\. {' \
    '        deny all;' \
    '    }' \
    '}' > /etc/nginx/conf.d/default.conf

# Create startup script
RUN cat > /usr/local/bin/entrypoint.sh <<'EOF' \
#!/bin/sh
set -e

cd /app/backend

# Generate a runtime-only Django secret
export DJANGO_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"

# Initialize database and import initial student data on first startup
if [ ! -f db.sqlite3 ]; then
    python3 manage.py migrate --noinput
    python3 manage.py import_marks data/students_marks.csv
else
    python3 manage.py migrate --noinput
fi

# Start Django application
gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 2 \
    --timeout 60 &

# Start Nginx in foreground
exec nginx -g 'daemon off;'
EOF
RUN chmod 755 /usr/local/bin/entrypoint.sh \
    && chown -R 101:101 /app

# Runtime directories and SQLite database are writable by UID 101.
# Nginx unprivileged image uses /tmp for PID and temporary files.

USER 101

EXPOSE 3000

CMD ["/usr/local/bin/entrypoint.sh"]
# # syntax=docker/dockerfile:1

# # ---------- Stage 1: build the React (Vite) frontend ----------
# FROM node:20-alpine AS frontend-build

# WORKDIR /fe

# COPY frontend/package*.json ./
# RUN npm ci

# COPY frontend/ ./
# RUN npm run build


# # ---------- Stage 2: Django API + nginx in one image ----------
# # Django 6 needs Python 3.12+
# FROM python:3.12-slim

# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1 \
#     PORT=3000

# RUN apt-get update \
#  && apt-get install -y --no-install-recommends nginx \
#  && rm -rf /var/lib/apt/lists/* \
#  && rm -f /etc/nginx/sites-enabled/default \
#  && ln -sf /dev/stdout /var/log/nginx/access.log \
#  && ln -sf /dev/stderr /var/log/nginx/error.log

# WORKDIR /app/backend

# # gunicorn isn't in requirements.txt, so install it here
# COPY backend/requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt gunicorn

# COPY backend/ ./

# # Built React app, served by nginx
# COPY --from=frontend-build /fe/dist /app/frontend-dist

# # nginx: serve the React app, proxy /api and /admin to gunicorn
# RUN cat > /app/nginx.conf.template <<'EOF'
# server {
#     listen __PORT__;
#     root /app/frontend-dist;
#     index index.html;

#     location ~ ^/(api|admin)/ {
#         proxy_pass http://127.0.0.1:8000;
#         proxy_set_header Host $http_host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }

#     # React router: unknown paths fall back to index.html
#     location / {
#         try_files $uri $uri/ /index.html;
#     }
# }
# EOF

# # Startup: migrate, import the CSV only on first run, then start gunicorn + nginx
# RUN cat > /app/start.sh <<'EOF'
# #!/bin/bash
# set -e
# cd /app/backend

# sed "s/__PORT__/${PORT}/" /app/nginx.conf.template > /etc/nginx/conf.d/app.conf

# python manage.py migrate --noinput

# # import_marks wipes the tables, so only run it when the DB is empty
# if ! python manage.py shell -c "import sys; from core.models import Student; sys.exit(0 if Student.objects.exists() else 1)"; then
#     python manage.py import_marks data/students_marks.csv
# fi

# gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --access-logfile - &
# nginx -g 'daemon off;' &

# trap 'kill $(jobs -p) 2>/dev/null' TERM INT
# wait -n
# exit $?
# EOF
# RUN chmod +x /app/start.sh

# EXPOSE 3000

# CMD ["/app/start.sh"]
