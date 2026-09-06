"""
00-UnifiedPortal: 動態應用模組註冊模型 (AppModule Model)
支援每週動態新增、排序、分類與狀態標籤管理
"""

from django.db import models
from django.utils.translation import get_language


class AppModule(models.Model):
    """應用模組註冊表 - 供大廳動態展示與 Nginx 路由映射"""

    STATUS_CHOICES = [
        ('active', '正式上線 (Active)'),
        ('beta', '公測體驗 (Beta)'),
        ('upcoming', '即將推出 (Coming Soon)'),
        ('maintenance', '維護中 (Maintenance)'),
    ]

    CATEGORY_CHOICES = [
        ('habit', '習慣養成與挑戰 (Habits & Challenges)'),
        ('learning', '學習與知識管理 (Learning & Knowledge)'),
        ('lifestyle', '生活與健康記錄 (Lifestyle & Health)'),
        ('creative', '創意與 AI 工具 (Creative & AI Tools)'),
        ('social', '社群與互動探索 (Community & Social)'),
        ('other', '其他專案 (Other Apps)'),
    ]

    # 基礎識別
    app_id = models.CharField('專案編號', max_length=20, unique=True, help_text='例如 "01", "02", "dietcontrol"')
    icon = models.CharField('圖示/Emoji', max_length=30, default='🚀', help_text='例如 "🔥", "📓", "📊", "🥗"')
    
    # 雙語名稱與簡介
    name_zh = models.CharField('應用名稱 (繁中)', max_length=100)
    name_en = models.CharField('應用名稱 (英文)', max_length=100)
    description_zh = models.TextField('功能簡介 (繁中)')
    description_en = models.TextField('功能簡介 (英文)')

    # 分類與路由
    category = models.CharField('應用分類', max_length=30, choices=CATEGORY_CHOICES, default='habit')
    route_path = models.CharField('訪問路徑 (URL Prefix)', max_length=100, help_text='例如 "/challenges/", "/journal/"')
    target_port = models.PositiveIntegerField('內部連接埠 (Host Port)', default=8001, help_text='例如 8001, 8002')

    # 狀態與排序
    status = models.CharField('營運狀態', max_length=20, choices=STATUS_CHOICES, default='active')
    is_new = models.BooleanField('標記為本週新品 (✨ NEW)', default=False)
    is_active = models.BooleanField('是否在大廳啟用顯示', default=True)
    display_order = models.PositiveIntegerField('顯示排序 (由小到大)', default=0)

    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    class Meta:
        verbose_name = '子應用模組'
        verbose_name_plural = '子應用模組清單 (App Registry)'
        ordering = ['display_order', 'app_id']

    def __str__(self):
        return f"[{self.app_id}] {self.name_zh} ({self.route_path})"

    @property
    def localized_name(self):
        """依據使用者目前語系自動輸出對應名稱"""
        lang = (get_language() or '').lower()
        if lang.startswith('en'):
            return self.name_en or self.name_zh
        return self.name_zh or self.name_en

    @property
    def localized_description(self):
        """依據使用者目前語系自動輸出對應簡介"""
        lang = (get_language() or '').lower()
        if lang.startswith('en'):
            return self.description_en or self.description_zh
        return self.description_zh or self.description_en

    @property
    def is_available(self):
        """是否可點擊進入 (active 或 beta)"""
        return self.status in ('active', 'beta')
