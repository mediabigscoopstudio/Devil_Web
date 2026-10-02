from rest_framework import serializers
from .models import Profile, ProfilePhoto, Interest, Preference, DatingIntent

class DatingIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatingIntent
        fields = ['code', 'label']

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePhoto
        fields = ['id', 'image', 'sort_order', 'is_primary']

class ProfileSerializer(serializers.ModelSerializer):
    photos = ProfilePhotoSerializer(many=True, read_only=True)
    interests = InterestSerializer(many=True, read_only=True)
    looking_for = DatingIntentSerializer(many=True, read_only=True)
    age = serializers.IntegerField(read_only=True)
    gender = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'display_name', 'age', 'date_of_birth', 'gender', 'looking_for', 'interests', 
            'photos', 'bio', 'city', 'country', 'location_enabled', 'profile_completed',
            'notifications_enabled', 'notifications_permission_status'
        ]
        
    def get_gender(self, obj):
        if not obj.gender:
            return None
        return {
            'code': obj.gender,
            'label': dict(Profile.GENDER_CHOICES).get(obj.gender, obj.gender)
        }

class ProfileUpdateSerializer(serializers.ModelSerializer):
    looking_for = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True
    )
    interests = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    
    class Meta:
        model = Profile
        fields = [
            'display_name', 'date_of_birth', 'gender', 'bio', 
            'looking_for', 'interests'
        ]

class LocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['location_latitude', 'location_longitude', 'city', 'country', 'location_enabled']

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['notifications_enabled', 'notifications_permission_status']

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ['minimum_age', 'maximum_age', 'maximum_distance_km', 'preferred_genders']
