"""
00-UnifiedPortal: 認證視圖
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout
from django.contrib import messages
from .services import GoogleAuthService, GoogleAuthError


class LoginView(View):
    """登入頁面視圖"""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        return render(request, self.template_name)


class GoogleLoginView(View):
    """觸發 Google OAuth 登入重導向"""

    def get(self, request):
        next_url = request.GET.get('next', '/')
        request.session['oauth_next_url'] = next_url
        try:
            auth_url = GoogleAuthService.get_auth_url()
            return redirect(auth_url)
        except GoogleAuthError as e:
            messages.error(request, str(e))
            return redirect('accounts:login')


class GoogleCallbackView(View):
    """Google OAuth 2.0 回調端點"""

    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')

        if error:
            messages.error(request, f"Google 授權失敗：{error}")
            return redirect('accounts:login')

        if not code:
            messages.error(request, "未獲取有效的 Google 授權碼。")
            return redirect('accounts:login')

        try:
            token_data = GoogleAuthService.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            profile = GoogleAuthService.get_user_profile(access_token)
            user = GoogleAuthService.get_or_create_google_user(profile)

            # 登入使用者建立 Session
            login(request, user)
            messages.success(request, f"歡迎回來，{user.first_name or user.username}！")

            next_url = request.session.pop('oauth_next_url', '/')
            return redirect(next_url)

        except GoogleAuthError as e:
            messages.error(request, f"登入失敗：{str(e)}")
            return redirect('accounts:login')
        except Exception:
            messages.error(request, "登入過程發生未知錯誤，請稍後重試。")
            return redirect('accounts:login')


class LogoutView(View):
    """登出視圖"""

    def post(self, request):
        logout(request)
        messages.info(request, "您已成功登出。")
        return redirect('/')
