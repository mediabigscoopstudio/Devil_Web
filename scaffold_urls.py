import os

base_dir = '/Volumes/Juggernut_Assist/Projects/Devil/Devil_web/Devil'

main_urls = '''from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API schema and docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # App API routes
    path('api/v1/auth/', include('Devil.accounts.urls')),
    # path('api/v1/profile/', include('Devil.profiles.urls')),
    # path('api/v1/discovery/', include('Devil.discovery.urls')),
    # path('api/v1/matches/', include('Devil.matching.urls')),
    # path('api/v1/conversations/', include('Devil.messaging.urls')),
    # path('api/v1/moderation/', include('Devil.moderation.urls')),
    # path('api/v1/notifications/', include('Devil.notifications.urls')),
]
'''

with open(os.path.join(base_dir, 'Devil', 'urls.py'), 'w') as f:
    f.write(main_urls)

accounts_urls = '''from django.urls import path
from .views import RequestOTPView, VerifyOTPView, MeView

urlpatterns = [
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('me/', MeView.as_view(), name='me'),
]
'''

with open(os.path.join(base_dir, 'accounts', 'urls.py'), 'w') as f:
    f.write(accounts_urls)

accounts_views = '''from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken

class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user, created = User.objects.get_or_create(phone_number=phone_number)
        return Response({'message': 'OTP sent successfully. (Use 00000 for MVP)'})

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')
        
        if not phone_number or not otp:
            return Response({'error': 'Phone number and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if otp != '00000':
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(phone_number=phone_number)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'phone_number': user.phone_number,
            'is_verified': user.is_verified,
            'status': user.status
        })
'''

with open(os.path.join(base_dir, 'accounts', 'views.py'), 'w') as f:
    f.write(accounts_views)
    
print("URLs and views scaffolded successfully.")
