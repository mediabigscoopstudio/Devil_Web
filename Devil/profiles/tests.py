from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from .models import Profile, Interest, DatingIntent, ProfilePhoto
import datetime

class ProfileOnboardingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone_number='+919999999999')
        self.profile = Profile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
        
        self.intent1 = DatingIntent.objects.create(code='casual_date', label='Casual Date')
        self.intent2 = DatingIntent.objects.create(code='exploring', label='Exploring')
        self.interest = Interest.objects.create(name='Music', slug='music')
        self.interest2 = Interest.objects.create(name='Art', slug='art')
        self.interest3 = Interest.objects.create(name='Gaming', slug='gaming')

    def test_get_profile(self):
        url = reverse('profile-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['profile']['profile_completed'])

    def test_update_profile_partial(self):
        url = reverse('profile-me')
        response = self.client.patch(url, {'display_name': 'Ketan', 'gender': 'man'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_name, 'Ketan')
        self.assertEqual(self.profile.gender, 'man')

    def test_update_age_under_18(self):
        url = reverse('profile-me')
        recent_date = (datetime.date.today() - datetime.timedelta(days=365*10)).strftime('%Y-%m-%d')
        response = self.client.patch(url, {'date_of_birth': recent_date})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'AGE_RESTRICTED')

    def test_profile_completion_fails_incomplete(self):
        url = reverse('profile-complete')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'PROFILE_INCOMPLETE')

    def test_profile_completion_success(self):
        self.profile.display_name = 'Ketan'
        self.profile.date_of_birth = datetime.date.today() - datetime.timedelta(days=365*20)
        self.profile.gender = 'man'
        self.profile.save()
        self.profile.looking_for.add(self.intent1)
        self.profile.interests.add(self.interest, self.interest2, self.interest3)
        
        # add photos
        for i in range(3):
            ProfilePhoto.objects.create(
                profile=self.profile,
                image=f'photo{i}.jpg',
                is_primary=(i==0),
                sort_order=i
            )

        url = reverse('profile-complete')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['profile_completed'])
        self.assertFalse(response.data['requires_onboarding'])

    def test_location_update(self):
        url = reverse('profile-location')
        response = self.client.patch(url, {
            'location_latitude': 28.6139,
            'location_longitude': 77.2090,
            'city': 'Delhi',
            'location_enabled': True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.city, 'Delhi')
        self.assertTrue(self.profile.location_enabled)

    def test_photo_upload_limit(self):
        for i in range(6):
            ProfilePhoto.objects.create(profile=self.profile, image=f'photo{i}.jpg', sort_order=i)
            
        url = reverse('photo-list-create')
        dummy_file = SimpleUploadedFile("file.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post(url, {'image': dummy_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'PHOTO_LIMIT_EXCEEDED')

    def test_delete_last_photo_fails(self):
        photo = ProfilePhoto.objects.create(profile=self.profile, image='photo.jpg')
        url = reverse('photo-detail', args=[photo.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'MIN_PHOTO_ERROR')
