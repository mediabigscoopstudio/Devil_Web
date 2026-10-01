from django.urls import path
from .views import RequestOTPView, VerifyOTPView, MeView

urlpatterns = [
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('me/', MeView.as_view(), name='me'),
]
