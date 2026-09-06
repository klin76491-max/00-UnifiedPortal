from django.urls import path
from .views import LoginView, GoogleLoginView, GoogleCallbackView, LogoutView

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google_callback'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
