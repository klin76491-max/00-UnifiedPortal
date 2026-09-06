#!/bin/sh
set -e

# 自動執行資料庫遷移
echo "Running database migrations..."
python manage.py migrate --noinput

# 自動編譯語言包 (若存在 compile_translations.py)
if [ -f "compile_translations.py" ]; then
    python compile_translations.py || true
fi

exec "$@"
