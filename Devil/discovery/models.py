from django.db import models
import uuid
from accounts.models import User

class Swipe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_received')
    action = models.CharField(max_length=20) # LIKE, PASS, SPECIAL_LIKE
    created_at = models.DateTimeField(auto_now_add=True)
