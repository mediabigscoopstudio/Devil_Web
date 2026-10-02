from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

class UserManager(BaseUserManager):
    def create_user(self, phone_number=None, email=None, password=None, **extra_fields):
        # Allow creating users without phone numbers for social login
        if not phone_number and not email:
            raise ValueError('Either Phone Number or Email must be set')
        user = self.model(phone_number=phone_number, email=self.normalize_email(email) if email else None, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number=phone_number, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('blocked', 'Blocked'),
        ('deleted', 'Deleted'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'

    def __str__(self):
        return self.phone_number or self.email or str(self.id)


class SocialIdentity(models.Model):
    PROVIDER_CHOICES = (
        ('google', 'Google'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_identities')
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['provider', 'provider_user_id'], name='unique_provider_user')
        ]

    def __str__(self):
        return f"{self.provider} - {self.email or self.provider_user_id}"

