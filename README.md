# 00-UnifiedPortal - 統一應用大廳與 SSO 服務 (Unified Hub & SSO)

**專案名稱**：A Little Wonder 統一應用大廳與單一登入中心  
**系統代號**：`00-UnifiedPortal`  
**推薦主機埠號**：`8000` (內部 8000 $\rightarrow$ 主機 8000)  
**主要技術**：Django 5.x LTS, Google OAuth 2.0, Nginx auth_request 整合, 繁中/英文 i18n  

---

## 🌟 核心功能特色

1. **🏨 全域統一登入 (SSO Gateway)**：
   - 採用 Google OAuth 2.0 一鍵授權，杜絕帳號密碼外洩風險。
   - 登入一次，即可透過 Nginx 安全網關暢行全站所有子專案。
2. **⚡ Nginx 內部認證端點 (`/api/auth-verify/`)**：
   - 專供 Nginx `auth_request` 模組在微秒內校驗 Session，安全傳遞已認證之 `REMOTE_USER` 與 Email。
3. **🚀 動態應用註冊中心 (Dynamic App Registry)**：
   - **每週新增專案 0 程式碼改動**：直接在 Django Admin 新增應用名稱、圖示、路由與狀態，大廳九宮格即時上架！
4. **🎨 A Little Wonder 頂級設計美學**：
   - 經典深海藍（`#1a3a52`）、青松藍綠（`#2d7a8a`）與活力橙調色盤。
   - 毛玻璃卡片、狀態徽章（`✨ NEW`、`即將推出`）、分類 Tab 快速篩選。
5. **🌐 完整中英雙語 (i18n)**：
   - 支援瀏覽器語系自動判定與頂部 `🌐 繁體中文 / English` 手動切換。

---

## 🚀 本地快速開始 (Local Quick Start)

### 1. 安裝套件與環境設定
```powershell
# 複製環境變數範本
Copy-Item .env.example .env

# 安裝依賴 (建議使用虛擬環境)
python -m pip install -r requirements.txt

# 執行資料庫遷移
python manage.py migrate

# 編譯多語系檔案
python compile_translations.py
```

### 2. 建立管理員帳號 (用以每週新增專案)
```powershell
python manage.py createsuperuser
```

### 3. 啟動開發伺服器
```powershell
python manage.py runserver 127.0.0.1:8000
```
訪問 `http://127.0.0.1:8000/` 即可進入應用大廳！

---

## 🐳 Docker 獨立微服務容器化運行

本專案具備完整獨立 Docker 支援：

### 1. 建置獨立映像檔
```bash
docker build -t alw-portal:latest .
```

### 2. 啟動容器 (映射本機 8081 埠)
```bash
# -d: 背景執行容器
# -p 127.0.0.1:8081:8000: 將本機 8081 映射到容器內的 8000 埠
# --env-file: 載入 .env 環境變數
# -e DJANGO_SUPERUSER_*: 首次啟動容器時自動建立 Django 超級管理員
# -v: 將 SQLite 資料庫持久化保存在本機 dockerVolumn/00-UnifiedPortal
docker run -d \
  --name alw-portal \
  -p 127.0.0.1:8081:8000 \
  --env-file .env \
  -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_EMAIL=admin@example.com \
  -e DJANGO_SUPERUSER_PASSWORD=adminpassword \
  -v "$PWD/../dockerVolumn/00-UnifiedPortal:/app/data" \
  --restart unless-stopped \
  alw-portal:latest
```

### 3. 查看運行狀態與日誌
```bash
# 查看容器狀態
docker ps -f name=alw-portal

# 查看即時日誌
docker logs -f alw-portal
```

### 4. 建立管理員帳號 (首次啟動)
```bash
docker exec -it alw-portal python manage.py createsuperuser
```

### 5. 停止與刪除容器
```bash
docker stop alw-portal && docker rm alw-portal
```

### 6. 在容器內執行自動化測試
```bash
docker exec -it alw-portal python manage.py test portal -v 2
```

---

## ⚡ 子專案生命週期管理：新增、下架與刪除 SOP

為因應每週高頻迭代需求，子系統的新增、維護與刪除均標準化為直覺 SOP：

### ➕ 一、每週新增子專案 (Add a Project) - 3 步驟

當您每週完成一個新系統（例如 `03-PersonalDataDashboard`，運行於 Port `8003`）時：

#### 步驟 1：啟動新子專案微服務容器 (僅綁定 127.0.0.1)
```bash
docker run -d \
  --name alw-app-03 \
  -p 127.0.0.1:8003:8000 \
  --env-file .env \
  -v alw_dashboard_data:/app \
  --restart unless-stopped \
  alw-personal-dashboard:latest
```

#### 步驟 2：在 Nginx 加入 1 個路由小檔 (`App/nginx/conf.d/apps/03-dashboard.conf`)
```nginx
location /dashboard/ {
    auth_request /internal_auth_verify;
    auth_request_set $user_email $upstream_http_x_user_email;
    auth_request_set $user_name  $upstream_http_x_user_name;

    proxy_pass http://127.0.0.1:8003/dashboard/;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $http_cf_connecting_ip;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;

    proxy_set_header REMOTE_USER $user_email;
    proxy_set_header X-User-Email $user_email;
    proxy_set_header X-User-Name $user_name;

    error_page 401 = @error401;
}
```
執行重新載入：
```bash
docker exec alw-nginx nginx -s reload
```

#### 步驟 3：在 Django Admin 後台登記上架 (0 程式碼改動)
1. 進入 Portal 後台：`https://hub.yourdomain.com/admin/`
2. 點擊 **「子應用模組清單」 $\rightarrow$ 「新增子應用模組」**：
   - **專案編號**：`03`
   - **Emoji 圖示**：`📊`
   - **繁中名稱 / 英文名稱**：`個人數據儀表板` / `Personal Data Dashboard`
   - **功能簡介 (繁中/英文)**：填寫簡短吸引人的功能描述
   - **應用分類**：選擇 `生活與健康記錄`
   - **訪問路徑**：`/dashboard/`
   - **內部連接埠**：`8003`
   - **營運狀態**：`正式上線 (active)`
   - **標記為本週新品**：勾選 `✨ NEW`（大廳卡片自動顯示亮眼新品標籤）
   - **顯示排序**：`3`
3. 點擊 **儲存** $\rightarrow$ **大廳首頁即刻呈現全新九宮格卡片，點擊直達該系統！**

---

### ⏸️ 二、暫時停用 / 維護下架 (Deactivate / Maintenance)

若特定專案需要暫時進行資料庫升級、功能修復或預告推出，**無需刪除容器或檔案**，直接由後台控制：

1. **方式 A：維護中模式 (Maintenance Mode)**：
   - 進入 Admin 後台將該應用的「營運狀態」改為 **`維護中 (Maintenance)`** 或 **`即將推出 (Coming Soon)`**。
   - **效果**：大廳卡片仍保留，但按鈕自動轉為灰色禁用狀態，顯示「維護中」或「即將推出」，避免使用者進入報錯。
2. **方式 B：完全隱藏 (Hide from Portal)**：
   - 進入 Admin 後台將該應用的 **「是否在大廳啟用顯示 (is_active)」** 取消勾選。
   - **效果**：大廳九宮格卡片瞬間隱藏，未來需要時隨時勾選即可 1 秒復原。

---

### 🗑️ 三、徹底下線與刪除專案 (Delete a Project Completely) - 3 步驟

若確定永久下線某個子系統：

#### 步驟 1：從 Portal 後台刪除登記
- 登入 `https://hub.yourdomain.com/admin/`，勾選該應用，選擇 **「刪除選取的子應用模組」** 並確認。
- 大廳九宮格即時移除該卡片。

#### 步驟 2：移除 Nginx 路由設定
```bash
# 刪除對應的設定檔
rm App/nginx/conf.d/apps/03-dashboard.conf

# 重新載入 Nginx
docker exec alw-nginx nginx -s reload
```

#### 步驟 3：停止並刪除子專案容器
```bash
# 停止並移除容器
docker stop alw-app-03
docker rm alw-app-03

# (可選) 若不再需要該專案的資料庫 Volume
docker volume rm alw_dashboard_data
```

---

## 🔑 Google OAuth 2.0 憑證配置

請至 [Google Cloud Console](https://console.cloud.google.com/) 建立 OAuth 2.0 Client ID：
1. **已授權的 JavaScript 來源**：`https://hub.yourdomain.com`（本地測試填 `http://127.0.0.1:8000`）
2. **已授權的重新導向 URI**：`https://hub.yourdomain.com/accounts/google/callback/`
3. 將 Client ID 與 Client Secret 填入 `.env` 檔案中。
