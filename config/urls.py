"""
URL configuration for 00-UnifiedPortal (統一應用大廳與 SSO 服務).
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')), # 語言切換端點
    path('accounts/', include('accounts.urls')),      # Google 登入認證
    path('', include('portal.urls')),                 # 九宮格大廳與驗證 API
]
