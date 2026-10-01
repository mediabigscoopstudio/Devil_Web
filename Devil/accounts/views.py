from rest_framework.views import APIView
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
            
        user, _ = User.objects.get_or_create(phone_number=phone_number)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id
        })

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
