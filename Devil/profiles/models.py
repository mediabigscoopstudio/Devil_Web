from django.db import models
import uuid
from accounts.models import User
from django.utils import timezone

class DatingIntent(models.Model):
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.label

class Interest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Profile(models.Model):
    GENDER_CHOICES = (
        ('woman', 'Woman'),
        ('man', 'Man'),
        ('non_binary', 'Non-Binary'),
        ('trans_woman', 'Trans Woman'),
        ('trans_man', 'Trans Man'),
        ('prefer_not_to_say', 'Prefer Not To Say'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, blank=True)
    bio = models.TextField(max_length=300, blank=True)
    
    # Location
    location_latitude = models.FloatField(null=True, blank=True)
    location_longitude = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    location_enabled = models.BooleanField(default=False)
    location_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    notifications_enabled = models.BooleanField(default=False)
    notifications_permission_status = models.CharField(max_length=30, default="unknown")
    
    # Relationships
    looking_for = models.ManyToManyField(DatingIntent, blank=True)
    interests = models.ManyToManyField(Interest, blank=True)
    
    is_discoverable = models.BooleanField(default=True)
    profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

class ProfilePhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='profile_photos/')
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Preference(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='preference')
    minimum_age = models.IntegerField(default=18)
    maximum_age = models.IntegerField(default=99)
    maximum_distance_km = models.IntegerField(default=50)
    preferred_genders = models.JSONField(default=list)
