#!/bin/sh
set -e

# 自動載入 .env 環境變數 (若存在)
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
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

exec "$@"
