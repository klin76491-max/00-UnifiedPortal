from django.urls import path
from .views import PortalHomeView, AuthVerifyAPIView

app_name = 'portal'

urlpatterns = [
    path('', PortalHomeView.as_view(), name='home'),
    path('api/auth-verify/', AuthVerifyAPIView.as_view(), name='auth_verify'),
]
