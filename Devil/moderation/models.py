from django.db import models
import uuid
from accounts.models import User

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
