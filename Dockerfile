FROM python:3.12-slim

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 設定工作目錄
WORKDIR /app

# 安裝相依套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案原始碼
COPY . .

# 賦予 entrypoint 執行權限
RUN chmod +x docker-entrypoint.sh

# 暴露 8000 埠號 (主機映射為 8000)
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
