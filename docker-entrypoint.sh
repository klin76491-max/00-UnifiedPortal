#!/bin/sh
set -e

# 自動載入 .env 環境變數 (若存在)
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

# 若配置 PostgreSQL，等待資料庫連線就緒
if [ -n "$DB_HOST" ] && [ "$USE_SQLITE" != "True" ] && [ "$USE_SQLITE" != "true" ]; then
    echo "Waiting for PostgreSQL ($DB_HOST:${DB_PORT:-5432}) to become ready..."
    python - <<'EOF'
import os
import socket
import time
import sys

host = os.getenv('DB_HOST', 'host.docker.internal')
port = int(os.getenv('DB_PORT', 5432))
timeout = 30
start = time.time()

while time.time() - start < timeout:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"Database port {host}:{port} is open and ready!")
            sys.exit(0)
    except (socket.timeout, ConnectionRefusedError, OSError):
        time.sleep(1)

print(f"Warning: Timed out waiting for database {host}:{port}, proceeding anyway...")
EOF
fi

# 自動執行資料庫遷移
echo "Running database migrations..."
python manage.py migrate --noinput

# 自動編譯語言包 (若存在 compile_translations.py)
if [ -f "compile_translations.py" ]; then
    python compile_translations.py || true
fi

# 自動建立 Django 超級管理員帳號 (若環境變數已設定)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser '$DJANGO_SUPERUSER_USERNAME' if not exists..."
    python manage.py createsuperuser --noinput || true
fi

# 自動從 apps.json 同步子專案模組清單
# 若掛載目錄中尚未有 apps.json，首次開機自動從範本 apps.example.json 初始化
if [ -n "$DATA_DIR" ] && [ ! -f "$DATA_DIR/apps.json" ] && [ -f "apps.example.json" ]; then
    echo "First time setup: Initializing $DATA_DIR/apps.json from apps.example.json..."
    cp apps.example.json "$DATA_DIR/apps.json" || true
fi

echo "Checking apps.json for dynamic app modules..."
python manage.py sync_apps --silent-if-missing || true

exec "$@"

