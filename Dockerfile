
# ---------- Stage 1: build the React (Vite) frontend ----------
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: nginx (port 3000) + Django/gunicorn, non-root ----------
FROM nginxinc/nginx-unprivileged:alpine
USER root

RUN apk add --no-cache python3 py3-pip bash

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt gunicorn==23.0.0

# Only what the API needs (no tests/scripts)
COPY backend/manage.py ./
COPY backend/config ./config
COPY backend/core ./core
COPY backend/data ./data

# nginx: serve the React build, proxy /api and /admin to gunicorn (only conf.d/default.conf is replaced)
RUN printf '%s\n' \
  'server {' \
  '  listen 3000;' \
  '  server_name _;' \
  '  server_tokens off;' \
  '  root /usr/share/nginx/html;' \
  '  index index.html;' \
  '  gzip on;' \
  '  gzip_types text/css application/javascript application/json image/svg+xml;' \
  '  location /api/ {' \
  '    proxy_pass http://127.0.0.1:8000;' \
  '    proxy_set_header Host $host;' \
  '    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
  '    proxy_set_header X-Forwarded-Proto $scheme;' \
  '  }' \
  '  location /admin/ {' \
  '    proxy_pass http://127.0.0.1:8000;' \
  '    proxy_set_header Host $host;' \
  '  }' \
  '  location /assets/ {' \
  '    expires 7d;' \
  '    add_header Cache-Control "public";' \
  '    try_files $uri =404;' \
  '  }' \
  '  location / {' \
  '    try_files $uri $uri/ /index.html;' \
  '  }' \
  '}' > /etc/nginx/conf.d/default.conf

# Start script: gunicorn (127.0.0.1:8000) + nginx (0.0.0.0:3000); container exits if either dies
RUN printf '%s\n' \
  '#!/bin/bash' \
  'cd /app/backend' \
  'python3 -m gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --access-logfile - &' \
  'nginx -g "daemon off;" &' \
  'trap "kill \$(jobs -p) 2>/dev/null; exit 0" TERM INT' \
  'wait -n' \
  'exit $?' > /app/start.sh \
  && chmod 755 /app/start.sh

# Build-time: DEBUG off, create the SQLite DB, load the CSV, make everything writable by user 101
RUN sed -i 's/^DEBUG = True/DEBUG = False/' config/settings.py \
 && python3 manage.py migrate --noinput \
 && python3 manage.py import_marks data/students_marks.csv \
 && chown -R 101:101 /app

COPY --from=frontend --chown=101:101 /build/dist/ /usr/share/nginx/html/

USER 101
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:3000/ || exit 1

CMD ["/app/start.sh"]

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
