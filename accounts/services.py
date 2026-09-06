"""
00-UnifiedPortal: Google OAuth 2.0 認證與使用者管理服務
"""

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction


class GoogleAuthError(Exception):
    """Google OAuth 認證錯誤"""
    pass


class GoogleAuthService:
    """Google OAuth 2.0 認證與使用者同步服務"""

    @staticmethod
    def get_auth_url(state: str = None) -> str:
        """產生 Google OAuth 登入重導向 URL"""
        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '')
        auth_url = getattr(settings, 'GOOGLE_AUTH_URL', 'https://accounts.google.com/o/oauth2/v2/auth')

        if not client_id:
            raise GoogleAuthError("未設定 GOOGLE_OAUTH_CLIENT_ID，請在環境變數或後台配置。")

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'online',
            'prompt': 'select_account',
        }
        if state:
            params['state'] = state

        from urllib.parse import urlencode
        return f"{auth_url}?{urlencode(params)}"

    @staticmethod
    def exchange_code_for_token(code: str) -> dict:
        """向 Google 伺服器使用 Authorization Code 交換 Access Token"""
        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
        client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '')
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '')
        token_url = getattr(settings, 'GOOGLE_TOKEN_URL', 'https://oauth2.googleapis.com/token')

        if not client_id or not client_secret:
            raise GoogleAuthError("Google OAuth Client ID 或 Secret 尚未設定。")

        try:
            resp = requests.post(
                token_url,
                data={
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code',
                },
                timeout=10
            )
            if resp.status_code != 200:
                raise GoogleAuthError(f"Google Token 交換失敗: {resp.text}")
            return resp.json()
        except requests.RequestException as e:
            raise GoogleAuthError(f"連線至 Google 認證伺服器失敗: {str(e)}")

    @staticmethod
    def get_user_profile(access_token: str) -> dict:
        """使用 Access Token 獲取 Google 使用者個人資訊 (Email, Name)"""
        userinfo_url = getattr(settings, 'GOOGLE_USERINFO_URL', 'https://www.googleapis.com/oauth2/v2/userinfo')
        try:
            resp = requests.get(
                userinfo_url,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            if resp.status_code != 200:
                raise GoogleAuthError(f"取得 Google 使用者資訊失敗: {resp.text}")
            return resp.json()
        except requests.RequestException as e:
            raise GoogleAuthError(f"連線至 Google 使用者資訊 API 失敗: {str(e)}")

    @classmethod
    def get_or_create_google_user(cls, profile: dict) -> User:
        """
        根據 Google 回傳資訊建立或登入 User
        - 以 Email 為核心識別依據
        - 自動同步 Google 姓名與 Email
        """
        email = profile.get('email')
        if not email:
            raise GoogleAuthError("Google 帳號未提供電子郵件地址。")

        full_name = profile.get('name', '')
        given_name = profile.get('given_name', '')
        family_name = profile.get('family_name', '')

        with transaction.atomic():
            user = User.objects.filter(email=email).first()
            if not user:
                # 建立新使用者，若 username 衝突自動遞增
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=given_name or full_name,
                    last_name=family_name
                )
                user.set_unusable_password()
                user.save()
            else:
                # 已存在使用者，更新姓名
                if full_name:
                    user.first_name = given_name or full_name
                    user.last_name = family_name
                    user.save(update_fields=['first_name', 'last_name'])

            return user
