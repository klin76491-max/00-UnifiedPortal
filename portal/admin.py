from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from .models import AppModule
from .management.commands.sync_apps import sync_apps_from_json


@admin.register(AppModule)
class AppModuleAdmin(admin.ModelAdmin):
    change_list_template = "admin/portal/appmodule/change_list.html"

    list_display = ('app_id', 'icon', 'name_zh', 'name_en', 'category', 'route_path', 'target_port', 'status', 'is_new', 'display_order', 'is_active')
    list_filter = ('category', 'status', 'is_new', 'is_active')
    search_fields = ('app_id', 'name_zh', 'name_en', 'description_zh', 'description_en', 'route_path')
    list_editable = ('status', 'is_new', 'display_order', 'is_active')
    ordering = ('display_order', 'app_id')

    fieldsets = (
        ('基本識別', {
            'fields': ('app_id', 'icon', 'category', 'display_order')
        }),
        ('繁體中文內容', {
            'fields': ('name_zh', 'description_zh')
        }),
        ('英文內容 (English)', {
            'fields': ('name_en', 'description_en')
        }),
        ('技術路由與連接埠', {
            'fields': ('route_path', 'target_port')
        }),
        ('營運狀態與標籤', {
            'fields': ('status', 'is_new', 'is_active')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sync-json/', self.admin_site.admin_view(self.sync_json_view), name='portal_appmodule_sync_json'),
        ]
        return custom_urls + urls

    def sync_json_view(self, request):
        """處理從 apps.json 重新同步之 Admin 視圖"""
        if not self.has_change_permission(request):
            raise PermissionDenied

        result = sync_apps_from_json()
        if result['success']:
            self.message_user(
                request,
                f"✅ 成功從 {result['file_path']} 同步應用模組！新增 {result['created']} 個、更新 {result['updated']} 個（共處理 {result['total']} 個）",
                messages.SUCCESS
            )
            if result.get('errors'):
                for err in result['errors']:
                    self.message_user(request, f"⚠️ {err}", messages.WARNING)
        else:
            self.message_user(
                request,
                f"❌ 同步失敗: {result.get('error', '未知錯誤')}",
                messages.ERROR
            )

        return HttpResponseRedirect(reverse('admin:portal_appmodule_changelist'))

