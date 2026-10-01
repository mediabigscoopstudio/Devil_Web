from django.db import models
import uuid
from accounts.models import User

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    location_latitude = models.FloatField(null=True, blank=True)
    location_longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, blank=True)
    is_discoverable = models.BooleanField(default=True)
    profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ProfilePhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='profile_photos/')
    sort_order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Interest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

class ProfileInterest(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='interests')
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)

class Preference(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='preference')
    minimum_age = models.IntegerField(default=18)
    maximum_age = models.IntegerField(default=99)
    maximum_distance_km = models.IntegerField(default=50)
    preferred_genders = models.JSONField(default=list)
