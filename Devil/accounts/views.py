import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import User, SocialIdentity
from .serializers import (
    UserSerializer, AuthResponseSerializer, OTPRequestSerializer, 
    OTPVerifySerializer, GoogleAuthSerializer
)

class AuthHelper:
    @staticmethod
    def get_tokens_for_user(user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def get_auth_response(user, is_new_user):
        requires_onboarding = True
        if hasattr(user, 'profile') and hasattr(user.profile, 'profile_completed'):
            requires_onboarding = not user.profile.profile_completed

        return {
            'success': True,
            'is_new_user': is_new_user,
            'requires_onboarding': requires_onboarding,
            'user': UserSerializer(user).data,
            'tokens': AuthHelper.get_tokens_for_user(user)
        }

class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        phone_number = serializer.validated_data['phone_number']
        # In MVP, we just pretend to send an OTP
        
        expose_otp = os.environ.get('DEVIL_EXPOSE_MVP_OTP', 'true').lower() == 'true'
        mvp_otp = os.environ.get('DEVIL_MVP_OTP', '00000')

        response_data = {
            'success': True,
            'message': 'OTP sent successfully.',
            'otp_required': True
        }
        
        if expose_otp:
            response_data['development_otp'] = mvp_otp
            
        return Response(response_data)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        phone_number = serializer.validated_data['phone_number']
        otp = serializer.validated_data['otp']
        
        mvp_otp = os.environ.get('DEVIL_MVP_OTP', '00000')
        if otp != mvp_otp:
            return Response({
                'success': False,
                'code': 'INVALID_OTP',
                'message': 'The OTP is invalid.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(phone_number=phone_number)
            is_new_user = False
        except User.DoesNotExist:
            user = User.objects.create_user(phone_number=phone_number)
            user.is_verified = True
            user.save()
            is_new_user = True
            
        if user.status != 'active':
            return Response({
                'success': False,
                'code': f'ACCOUNT_{user.status.upper()}',
                'message': f'This account is currently {user.status}.'
            }, status=status.HTTP_403_FORBIDDEN)
            
        return Response(AuthHelper.get_auth_response(user, is_new_user))


class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input.'
            }, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['id_token']
        client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        
        try:
            # We skip client_id verification here if not configured, but ideally we should verify it
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id if client_id else None)
            
            provider_user_id = idinfo['sub']
            email = idinfo.get('email')
            
            is_new_user = False
            try:
                identity = SocialIdentity.objects.get(provider='google', provider_user_id=provider_user_id)
                user = identity.user
            except SocialIdentity.DoesNotExist:
                # Create a new user
                user = User.objects.create_user(email=email)
                user.is_verified = True
                user.save()
                SocialIdentity.objects.create(
                    user=user, 
                    provider='google', 
                    provider_user_id=provider_user_id,
                    email=email
                )
                is_new_user = True

            if user.status != 'active':
                return Response({
                    'success': False,
                    'code': f'ACCOUNT_{user.status.upper()}',
                    'message': f'This account is currently {user.status}.'
                }, status=status.HTTP_403_FORBIDDEN)

            return Response(AuthHelper.get_auth_response(user, is_new_user))
            
        except ValueError as e:
            return Response({
                'success': False,
                'code': 'GOOGLE_TOKEN_INVALID',
                'message': 'The Google token is invalid or expired.'
            }, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        requires_onboarding = True
        profile_completed = False
        if hasattr(user, 'profile') and hasattr(user.profile, 'profile_completed'):
            profile_completed = user.profile.profile_completed
            requires_onboarding = not profile_completed
            
        return Response({
            'success': True,
            'user': UserSerializer(user).data,
            'account': {
                'requires_onboarding': requires_onboarding,
                'profile_completed': profile_completed
            }
        })
