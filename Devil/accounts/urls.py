from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RequestOTPView, VerifyOTPView, MeView, GoogleAuthView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"success": True, "message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"success": False, "message": "Invalid token or logout failed."}, status=status.HTTP_400_BAD_REQUEST)

urlpatterns = [
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('google/', GoogleAuthView.as_view(), name='google'),
    path('me/', MeView.as_view(), name='me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
