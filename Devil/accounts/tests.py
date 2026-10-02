from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from .models import User, SocialIdentity
from profiles.models import Profile

class AuthAccountStateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
    def test_new_phone_account(self):
        url = reverse('verify-otp')
        data = {'phone_number': '+919876543210', 'otp': '00000'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user = User.objects.get(phone_number='+919876543210')
        self.assertTrue(Profile.objects.filter(user=user).exists())
        profile = Profile.objects.get(user=user)
        self.assertFalse(profile.profile_completed)
        
        self.assertTrue(response.data['is_new_user'])
        self.assertTrue(response.data['requires_onboarding'])

    def test_existing_incomplete_phone_account(self):
        user = User.objects.create_user(phone_number='+911111111111')
        user.is_verified = True
        user.save()
        Profile.objects.create(user=user, profile_completed=False)

        url = reverse('verify-otp')
        data = {'phone_number': '+911111111111', 'otp': '00000'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertFalse(response.data['is_new_user'])
        self.assertTrue(response.data['requires_onboarding'])

    def test_existing_completed_phone_account(self):
        user = User.objects.create_user(phone_number='+912222222222')
        user.is_verified = True
        user.save()
        Profile.objects.create(user=user, profile_completed=True)

        url = reverse('verify-otp')
        data = {'phone_number': '+912222222222', 'otp': '00000'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertFalse(response.data['is_new_user'])
        self.assertFalse(response.data['requires_onboarding'])

    def test_existing_user_without_profile(self):
        user = User.objects.create_user(phone_number='+913333333333')
        user.is_verified = True
        user.save()

        url = reverse('verify-otp')
        data = {'phone_number': '+913333333333', 'otp': '00000'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertTrue(Profile.objects.filter(user=user).exists())
        profile = Profile.objects.get(user=user)
        self.assertFalse(profile.profile_completed)
        self.assertTrue(response.data['requires_onboarding'])

    def test_auth_me_incomplete(self):
        user = User.objects.create_user(phone_number='+914444444444')
        user.is_verified = True
        user.save()
        Profile.objects.create(user=user, profile_completed=False)
        
        self.client.force_authenticate(user=user)
        url = reverse('me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertTrue(response.data['account']['requires_onboarding'])
        self.assertFalse(response.data['account']['profile_completed'])

    def test_auth_me_complete(self):
        user = User.objects.create_user(phone_number='+915555555555')
        user.is_verified = True
        user.save()
        Profile.objects.create(user=user, profile_completed=True)
        
        self.client.force_authenticate(user=user)
        url = reverse('me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertFalse(response.data['account']['requires_onboarding'])
        self.assertTrue(response.data['account']['profile_completed'])

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_new_user(self, mock_verify):
        mock_verify.return_value = {
            'sub': 'google123',
            'email': 'newuser@google.com'
        }
        
        url = reverse('google')
        data = {'id_token': 'fake_token'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user = User.objects.get(email='newuser@google.com')
        self.assertTrue(SocialIdentity.objects.filter(provider='google', provider_user_id='google123').exists())
        self.assertTrue(Profile.objects.filter(user=user).exists())
        
        self.assertTrue(response.data['is_new_user'])
        self.assertTrue(response.data['requires_onboarding'])

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_existing_user(self, mock_verify):
        user = User.objects.create_user(email='existing@google.com')
        user.is_verified = True
        user.save()
        SocialIdentity.objects.create(user=user, provider='google', provider_user_id='google456', email='existing@google.com')
        Profile.objects.create(user=user, profile_completed=True)
        
        mock_verify.return_value = {
            'sub': 'google456',
            'email': 'existing@google.com'
        }
        
        url = reverse('google')
        data = {'id_token': 'fake_token'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertFalse(response.data['is_new_user'])
        self.assertFalse(response.data['requires_onboarding'])
