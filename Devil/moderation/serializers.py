from rest_framework import serializers
from .models import Block, Report, ModerationAction

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ['id', 'blocker', 'blocked', 'created_at']
        read_only_fields = ['blocker']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'reporter', 'reported_user', 'reason', 'description', 'status', 'created_at']
        read_only_fields = ['reporter', 'status']
