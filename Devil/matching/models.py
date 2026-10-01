from django.db import models
import uuid
from accounts.models import User

class Match(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_one = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_user_one')
    user_two = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_user_two')
    matched_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
