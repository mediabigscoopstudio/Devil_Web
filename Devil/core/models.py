from django.db import models
import uuid
from accounts.models import User

class DeviceSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device_id = models.CharField(max_length=255)
    platform = models.CharField(max_length=50)
    app_version = models.CharField(max_length=50)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
