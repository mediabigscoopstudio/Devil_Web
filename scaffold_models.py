import os

base_dir = '/Volumes/Juggernut_Assist/Projects/Devil/Devil_web/Devil'

models_accounts = '''from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

class UserManager(BaseUserManager):
    def create_user(self, phone_number, email=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number must be set')
        user = self.model(phone_number=phone_number, email=self.normalize_email(email), **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('BANNED', 'Banned'),
        ('DELETED', 'Deleted'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
'''

models_profiles = '''from django.db import models
import uuid
from Devil.accounts.models import User

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
'''

models_discovery = '''from django.db import models
import uuid
from Devil.accounts.models import User

class Swipe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_received')
    action = models.CharField(max_length=20) # LIKE, PASS, SPECIAL_LIKE
    created_at = models.DateTimeField(auto_now_add=True)
'''

models_matching = '''from django.db import models
import uuid
from Devil.accounts.models import User

class Match(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_one = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_user_one')
    user_two = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_user_two')
    matched_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''

models_messaging = '''from django.db import models
import uuid
from Devil.accounts.models import User
from Devil.matching.models import Match

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, default='TEXT')
    text = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''

models_moderation = '''from django.db import models
import uuid
from Devil.accounts.models import User

class Block(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_created')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_submitted')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports_resolved')
    resolution_note = models.TextField(blank=True)

class ModerationAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_actions_taken')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_actions_received')
    action = models.CharField(max_length=50)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
'''

models_notifications = '''from django.db import models
import uuid
from Devil.accounts.models import User

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
'''

models_core = '''from django.db import models
import uuid
from Devil.accounts.models import User

class DeviceSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device_id = models.CharField(max_length=255)
    platform = models.CharField(max_length=50)
    app_version = models.CharField(max_length=50)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
'''

app_models = {
    'accounts': models_accounts,
    'profiles': models_profiles,
    'discovery': models_discovery,
    'matching': models_matching,
    'messaging': models_messaging,
    'moderation': models_moderation,
    'notifications': models_notifications,
    'core': models_core,
}

for app, content in app_models.items():
    file_path = os.path.join(base_dir, app, 'models.py')
    with open(file_path, 'w') as f:
        f.write(content)
        
print("Models scaffolded successfully.")
