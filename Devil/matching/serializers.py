from rest_framework import serializers
from .models import Match
from profiles.serializers import ProfileSerializer

class MatchSerializer(serializers.ModelSerializer):
    other_user_profile = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ['id', 'matched_at', 'is_active', 'other_user_profile']

    def get_other_user_profile(self, obj):
        request_user = self.context.get('request').user
        other_user = obj.user_two if obj.user_one == request_user else obj.user_one
        if hasattr(other_user, 'profile'):
            return ProfileSerializer(other_user.profile).data
        return None
