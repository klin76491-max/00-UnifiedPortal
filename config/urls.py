"""
URL configuration for 00-UnifiedPortal (統一應用大廳與 SSO 服務).
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')), # 語言切換端點
    path('accounts/', include('accounts.urls')),      # Google 登入認證
    path('', include('portal.urls')),                 # 九宮格大廳與驗證 API
]

from django.conf import settings
from django.views.static import serve
from django.urls import re_path

urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
]

