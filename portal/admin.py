from django.contrib import admin
from .models import AppModule


@admin.register(AppModule)
class AppModuleAdmin(admin.ModelAdmin):
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
