from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from .models import Profile, Interest, DatingIntent, ProfilePhoto
import datetime
from PIL import Image
import io

def generate_test_image(width=300, height=300, format='JPEG', size_mb=0):
    img = Image.new('RGB', (width, height), color='red')
    img_io = io.BytesIO()
    img.save(img_io, format=format)
    
    if size_mb > 0:
        img_io.write(b'\0' * int(size_mb * 1024 * 1024))
        
    img_io.seek(0)
    return SimpleUploadedFile(f"test.{format.lower()}", img_io.read(), content_type=f"image/{format.lower()}")

class ProfileOnboardingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone_number='+919999999999')
        self.profile = Profile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
        
        self.intent1 = DatingIntent.objects.create(code='casual_date', label='Casual Date')
        self.intent2 = DatingIntent.objects.create(code='exploring', label='Exploring')
        
        self.interest = Interest.objects.create(name='Music', slug='music', sort_order=1)
        self.interest2 = Interest.objects.create(name='Art', slug='art', sort_order=2)
        self.interest3 = Interest.objects.create(name='Gaming', slug='gaming', sort_order=3)
        self.interest4 = Interest.objects.create(name='Travel', slug='travel', sort_order=4)

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

    def test_update_bio_too_long(self):
        url = reverse('profile-me')
        response = self.client.patch(url, {'bio': 'a' * 301})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'BIO_TOO_LONG')

    def test_invalid_interests(self):
        url = reverse('profile-me')
        response = self.client.patch(url, {'interests': [self.interest.id, 99999]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVALID_INTERESTS')

    def test_too_many_interests(self):
        url = reverse('profile-me')
        # We need 11 interests to test max 10
        interests = [Interest.objects.create(name=f'Int{i}', slug=f'int{i}') for i in range(11)]
        response = self.client.patch(url, {'interests': [i.id for i in interests]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INTEREST_LIMIT')

    def test_invalid_dating_intents(self):
        url = reverse('profile-me')
        response = self.client.patch(url, {'looking_for': ['casual_date', 'fake_intent']})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVALID_DATING_INTENTS')

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
        
        # add photos safely bypassing validation for setup
        for i in range(3):
            ProfilePhoto.objects.create(
                profile=self.profile,
                image=generate_test_image(),
                is_primary=(i==0),
                sort_order=i
            )

        url = reverse('profile-complete')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['profile_completed'])
        self.assertFalse(response.data['requires_onboarding'])
        
        # Idempotent check
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_location_update(self):
        url = reverse('profile-location')
        response = self.client.patch(url, {
            'latitude': 28.6139,
            'longitude': 77.2090,
            'city': 'Delhi',
            'location_enabled': True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.city, 'Delhi')
        self.assertTrue(self.profile.location_enabled)
        self.assertEqual(self.profile.location_latitude, 28.6139)
        
    def test_location_invalid_coords(self):
        url = reverse('profile-location')
        response = self.client.patch(url, {'latitude': 999.0, 'longitude': 999.0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVALID_LOCATION')

    def test_photo_upload_valid(self):
        url = reverse('photo-list-create')
        file = generate_test_image()
        response = self.client.post(url, {'image': file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.profile.photos.count(), 1)
        self.assertTrue(self.profile.photos.first().is_primary)
        
    def test_photo_upload_too_small(self):
        url = reverse('photo-list-create')
        file = generate_test_image(width=100, height=100)
        response = self.client.post(url, {'image': file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVALID_IMAGE')
        
    def test_photo_upload_too_large_bytes(self):
        url = reverse('photo-list-create')
        file = generate_test_image(size_mb=11)
        response = self.client.post(url, {'image': file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'IMAGE_TOO_LARGE')

    def test_photo_upload_corrupted(self):
        url = reverse('photo-list-create')
        file = SimpleUploadedFile("fake.jpg", b"not_an_image", content_type="image/jpeg")
        response = self.client.post(url, {'image': file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVALID_IMAGE')

    def test_delete_last_photo_fails(self):
        photo = ProfilePhoto.objects.create(profile=self.profile, image=generate_test_image(), is_primary=True, sort_order=0)
        url = reverse('photo-detail', args=[photo.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'MIN_PHOTO_ERROR')

    def test_photo_reordering(self):
        p1 = ProfilePhoto.objects.create(profile=self.profile, image=generate_test_image(), is_primary=True, sort_order=0)
        p2 = ProfilePhoto.objects.create(profile=self.profile, image=generate_test_image(), is_primary=False, sort_order=1)
        p3 = ProfilePhoto.objects.create(profile=self.profile, image=generate_test_image(), is_primary=False, sort_order=2)
        
        url = reverse('photo-detail', args=[p3.id])
        response = self.client.patch(url, {'sort_order': 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        p1.refresh_from_db()
        p2.refresh_from_db()
        p3.refresh_from_db()
        
        self.assertEqual(p3.sort_order, 0)
        self.assertEqual(p1.sort_order, 1)
        self.assertEqual(p2.sort_order, 2)
        
    def test_invalid_photo_sort_order(self):
        p1 = ProfilePhoto.objects.create(profile=self.profile, image=generate_test_image(), is_primary=True, sort_order=0)
        p2 = ProfilePhoto.objects.create(profile=self.profile, image=generate_test_image(), is_primary=False, sort_order=1)
        
        url = reverse('photo-detail', args=[p2.id])
        
        # Test negative
        response = self.client.patch(url, {'sort_order': -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVALID_SORT_ORDER')
        
        # Test out of range (>= photo_count)
        response = self.client.patch(url, {'sort_order': 2})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'INVALID_SORT_ORDER')
        
    def test_delete_primary_reassigns(self):
        p1 = ProfilePhoto.objects.create(profile=self.profile, image=generate_test_image(), is_primary=True, sort_order=0)
        p2 = ProfilePhoto.objects.create(profile=self.profile, image=generate_test_image(), is_primary=False, sort_order=1)
        
        url = reverse('photo-detail', args=[p1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        p2.refresh_from_db()
        self.assertTrue(p2.is_primary)
        self.assertEqual(p2.sort_order, 0)
