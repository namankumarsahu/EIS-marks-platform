# syntax=docker/dockerfile:1

# ---------- Stage 1: build the React (Vite) frontend ----------
FROM node:20-alpine AS frontend-build

WORKDIR /fe

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ---------- Stage 2: Django API + nginx in one image ----------
# Django 6 needs Python 3.12+
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=3000

RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx \
 && rm -rf /var/lib/apt/lists/* \
 && rm -f /etc/nginx/sites-enabled/default \
 && ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log

WORKDIR /app/backend

# gunicorn isn't in requirements.txt, so install it here
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/ ./

# Built React app, served by nginx
COPY --from=frontend-build /fe/dist /app/frontend-dist

# nginx: serve the React app, proxy /api and /admin to gunicorn
RUN cat > /app/nginx.conf.template <<'EOF'
server {
    listen __PORT__;
    root /app/frontend-dist;
    index index.html;

    location ~ ^/(api|admin)/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # React router: unknown paths fall back to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# Startup: migrate, import the CSV only on first run, then start gunicorn + nginx
RUN cat > /app/start.sh <<'EOF'
#!/bin/bash
set -e
cd /app/backend

sed "s/__PORT__/${PORT}/" /app/nginx.conf.template > /etc/nginx/conf.d/app.conf

python manage.py migrate --noinput

# import_marks wipes the tables, so only run it when the DB is empty
if ! python manage.py shell -c "import sys; from core.models import Student; sys.exit(0 if Student.objects.exists() else 1)"; then
    python manage.py import_marks data/students_marks.csv
fi

gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --access-logfile - &
nginx -g 'daemon off;' &

trap 'kill $(jobs -p) 2>/dev/null' TERM INT
wait -n
exit $?
EOF
RUN chmod +x /app/start.sh

EXPOSE 3000

CMD ["/app/start.sh"]
