"""
Comprehensive Unit Tests for 00-UnifiedPortal:
1. Portal AuthVerify API (Nginx auth_request integration)
2. AppModule Dynamic Registry (CRUD, localized fields, ordering, active state)
3. GoogleAuthService and User JIT Provisioning
4. Accounts Views (LoginView, LogoutView)
5. Multi-language i18n switching and cookie persistence
"""

from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from portal.models import AppModule
from accounts.services import GoogleAuthService, GoogleAuthError


class PortalAuthVerifyTestCase(TestCase):
    """1. 測試 Nginx auth_request 內部毫秒校驗端點"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='kai@example.com',
            email='kai@example.com',
            first_name='Kai',
            last_name='Lin'
        )

    def test_auth_verify_unauthenticated_returns_401(self):
        """未登入訪客存取 /api/auth-verify/ 必須回傳 401 Unauthorized"""
        response = self.client.get(reverse('portal:auth_verify'))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode(), "Unauthorized")

    def test_auth_verify_authenticated_returns_200_with_headers(self):
        """已登入使用者存取 /api/auth-verify/ 必須回傳 200 並附帶 X-User 標頭"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('portal:auth_verify'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-User-Email'], 'kai@example.com')
        self.assertEqual(response['X-User-Name'], 'Kai')
        self.assertEqual(response['X-User-Id'], str(self.user.id))


class AppModuleRegistryTestCase(TestCase):
    """2. 測試動態 App 模組資料庫與大廳渲染"""

    def setUp(self):
        self.client = Client()
        self.active_app = AppModule.objects.create(
            app_id='01',
            icon='🔥',
            name_zh='粉絲挑戰打卡系統',
            name_en='Fans Challenge Check-in',
            description_zh='每日打卡挑戰',
            description_en='Daily check-in challenges',
            category='habit',
            route_path='/challenges/',
            target_port=8001,
            status='active',
            is_new=True,
            display_order=1,
            is_active=True,
        )
        self.upcoming_app = AppModule.objects.create(
            app_id='02',
            icon='📓',
            name_zh='AI 學習日誌系統',
            name_en='AI Learning Journal',
            description_zh='子彈思考筆記',
            description_en='Bullet journal with AI coaching',
            category='learning',
            route_path='/journal/',
            target_port=8002,
            status='upcoming',
            display_order=2,
            is_active=True,
        )
        self.hidden_app = AppModule.objects.create(
            app_id='99',
            icon='🧪',
            name_zh='測試隱藏應用',
            name_en='Hidden Test App',
            description_zh='未開放',
            description_en='Not open',
            category='other',
            route_path='/test/',
            target_port=8099,
            status='maintenance',
            display_order=99,
            is_active=False, # 停用顯示
        )

    def test_home_page_renders_active_apps_only(self):
        """首頁只會渲染 is_active=True 的子應用，隱藏停用的應用"""
        response = self.client.get(reverse('portal:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '粉絲挑戰打卡系統')
        self.assertContains(response, 'AI 學習日誌系統')
        self.assertContains(response, '✨ NEW')
        self.assertNotContains(response, '測試隱藏應用')

    def test_app_model_properties(self):
        """測試 AppModule 的計算屬性 (is_available, localized_name)"""
        self.assertTrue(self.active_app.is_available)
        self.assertFalse(self.upcoming_app.is_available)
        self.assertEqual(self.active_app.localized_name, '粉絲挑戰打卡系統')

    def test_home_page_english_translation(self):
        """切換為英文語系時，卡片標題與描述自動輸出英文版本"""
        self.client.post(
            reverse('set_language'),
            {'language': 'en', 'next': reverse('portal:home')},
            follow=True
        )
        response = self.client.get(reverse('portal:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fans Challenge Check-in')
        self.assertContains(response, 'AI Learning Journal')
        self.assertContains(response, 'Active Apps')


class GoogleAuthServiceTestCase(TestCase):
    """3. 測試 Google OAuth 2.0 服務與使用者自動建檔 (JIT Provisioning)"""

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='test-client-id')
    def test_get_auth_url(self):
        """測試 Google 授權跳轉網址產生"""
        url = GoogleAuthService.get_auth_url()
        self.assertIn('https://accounts.google.com/o/oauth2/v2/auth', url)
        self.assertIn('scope=openid+email+profile', url)

    def test_get_or_create_google_user_new(self):
        """首次 Google 登入自動建立全新使用者"""
        profile = {
            'email': 'newuser@gmail.com',
            'name': 'New User',
            'given_name': 'New',
            'family_name': 'User'
        }
        user = GoogleAuthService.get_or_create_google_user(profile)
        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, 'newuser@gmail.com')
        self.assertEqual(user.first_name, 'New')
        self.assertFalse(user.has_usable_password())

    def test_get_or_create_google_user_existing(self):
        """已存在使用者登入自動同步姓名資訊"""
        existing = User.objects.create_user(
            username='existinguser',
            email='existing@gmail.com',
            first_name='OldName'
        )
        profile = {
            'email': 'existing@gmail.com',
            'name': 'Updated Name',
            'given_name': 'Updated',
            'family_name': 'Name'
        }
        user = GoogleAuthService.get_or_create_google_user(profile)
        self.assertEqual(user.id, existing.id)
        self.assertEqual(user.first_name, 'Updated')


class AccountsViewsTestCase(TestCase):
    """4. 測試帳號登入與登出視圖"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com')

    def test_login_page_renders_google_button(self):
        """登入頁面必須包含 Google 一鍵登入按鈕且不含本地密碼表單"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '使用 Google 帳號一鍵登入')
        self.assertNotContains(response, 'type="password"')

    def test_logout_view_clears_session(self):
        """登出後清除 Session 並重導向至大廳"""
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
