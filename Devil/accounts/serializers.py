from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'is_verified', 'status']

class AuthResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    is_new_user = serializers.BooleanField()
    requires_onboarding = serializers.BooleanField()
    user = UserSerializer()
    tokens = serializers.DictField()

class OTPRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

class OTPVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=10)

class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()
