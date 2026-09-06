"""
00-UnifiedPortal: 視圖層
1. PortalHomeView: 應用大廳九宮格首頁
2. AuthVerifyAPIView: 專供 Nginx auth_request 內部毫秒校驗之端點
"""

from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import ListView
from .models import AppModule


class PortalHomeView(ListView):
    """應用大廳首頁 - 動態展示所有已註冊啟用的子系統卡片"""
    model = AppModule
    template_name = 'portal/home.html'
    context_object_name = 'apps'

    def get_queryset(self):
        return AppModule.objects.filter(is_active=True).order_by('display_order', 'app_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        apps = context['apps']
        
        # 統計資訊
        context['total_apps_count'] = apps.count()
        context['active_apps_count'] = apps.filter(status='active').count()
        context['new_apps_count'] = apps.filter(is_new=True).count()
        
        # 取得所有使用中的分類清單供前端 Tab 篩選
        categories = []
        for cat_key, cat_name in AppModule.CATEGORY_CHOICES:
            if apps.filter(category=cat_key).exists():
                categories.append({
                    'key': cat_key,
                    'name': cat_name,
                    'count': apps.filter(category=cat_key).count()
                })
        context['categories'] = categories

        return context


class AuthVerifyAPIView(View):
    """
    Nginx 內部認證端點 - GET /api/auth-verify/
    專供 Nginx 的 auth_request 模組進行內部毫秒校驗

    回傳規範：
    - 已登入：HTTP 200 OK，並在 Header 附帶 X-User-Email, X-User-Name, X-User-Id
    - 未登入：HTTP 401 Unauthorized，觸發 Nginx 302 重導向至 Portal 登入頁
    """

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            response = HttpResponse(status=200)
            email = request.user.email or request.user.username
            name = request.user.first_name or request.user.username
            user_id = str(request.user.id)

            response['X-User-Email'] = email
            response['X-User-Name'] = name
            response['X-User-Id'] = user_id
            return response
        else:
            return HttpResponse("Unauthorized", status=401)
